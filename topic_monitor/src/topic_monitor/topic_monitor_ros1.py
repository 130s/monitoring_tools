# Copyright 2016 Open Source Robotics Foundation, Inc.
# Copyright 2022 Kinu Garage
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import rospy
from std_msgs.msg import Float32, Header
from threading import Lock, Thread

## For some reason the following '%PKG%.%MODULE% fails when executed via
## 'rosrun', but not by Python w/o rosrun. Haven't dug deeper. Tracked in
## https://github.com/130s/monitoring_tools/issues/1
#from topic_monitor.topic_monitor import AbstDataReceivingThread, TopicMonitor
from topic_monitor import AbstDataReceivingThread, MonitoredTopic, TopicMonitor


class DataReceivingThread(Thread):

    def __init__(self, topic_monitor_ros1, options, node_name="topic_monitor_ros1_ros1"):
        super(DataReceivingThread, self).__init__()
        self.topic_monitor_ros1 = topic_monitor_ros1
        self.options = options
        self._node_name = node_name

    def run(self):
        rospy.init_node(self._node_name)
        try:
            self.topic_monitor_ros1.run_topic_listening(
                None, self.topic_monitor_ros1, self.options)
        except KeyboardInterrupt:
            self.stop()
            raise

    def stop(self):
        # Ref. http://wiki.ros.org/rospy/Overview/Initialization%20and%20Shutdown#Manual_shutdown_.28Advanced.29
        rospy.signal_shutdown("DataReceivingThread is termininating.")


class TopicMonitorRos1(TopicMonitor):
    """
    @note: Due to the history where the code went through refactoring what was
        originally written for ROS2, there can be things that are unnecessary
        for ROS1.
    """

    def add_monitored_topic(
            self, topic_type, topic_name, 
            expected_period=1.0, allowed_latency=1.0, stale_time=1.0,
            node=None, qos_profile=None):
        # Create a subscription to the topic
        monitored_topic = MonitoredTopic(topic_name, stale_time, lock=self.monitored_topics_lock)

        rospy.loginfo('Subscribing to topic: {}'.format(topic_name))
        sub = rospy.Subscriber(topic_name,
                               topic_type,
                               monitored_topic.topic_data_callback)

        # Create a timer for maintaining the expected value received on the topic
        expected_value_timer = node.create_timer(
            expected_period, monitored_topic.increment_expected_value)
        expected_value_timer.cancel()

        # Create a one-shot timer that won't start the expected value timer until the allowed
        # latency has elapsed
        allowed_latency_timer = node.create_timer(
            allowed_latency, monitored_topic.allowed_latency_timer_callback)
        allowed_latency_timer.cancel()

        # Create a publisher for the reception rate of the topic
        reception_rate_topic_name = self.reception_rate_topic_name + topic_name

        # TODO(dhood): remove this workaround
        # once https://github.com/ros2/rmw_connext/issues/234 is resolved
        reception_rate_topic_name += '_'

        node.get_logger().info(
            'Publishing reception rate on topic: %s' % reception_rate_topic_name)
        reception_rate_publisher = node.create_publisher(
            Float32, reception_rate_topic_name, 10)

        with self.monitored_topics_lock:
            monitored_topic.expected_value_timer = expected_value_timer
            monitored_topic.allowed_latency_timer = allowed_latency_timer
            self.publishers[topic_name] = reception_rate_publisher
            self.monitored_topics[topic_name] = monitored_topic

    def run_topic_listening(self, topic_monitor_ros1, options, node=None):
        while not rospy.is_shutdown():        
            # Check if there is a new topic online
            topic_names_and_types = rospy.get_published_topics()
            for topic_name, type_name in topic_names_and_types:
                # Infer the appropriate QoS profile from the topic name
                topic_info = topic_monitor_ros1.get_topic_info(topic_name)
                if topic_info is None:
                    # The topic is not for being monitored
                    continue

                is_new_topic = topic_name and topic_name not in topic_monitor_ros1.monitored_topics
                if is_new_topic:
                    topic_monitor_ros1.add_monitored_topic(
                        Header, topic_name,
                        options.expected_period, options.allowed_latency, options.stale_time,
                        node=None, qos_profile=None)

            # Wait for messages with a timeout, otherwise this thread will block any other threads
            # until a message is received
            rospy.loginfo("Right before rospy.spin()")
            rospy.spin()
