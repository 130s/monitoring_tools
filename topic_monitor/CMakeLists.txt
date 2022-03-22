cmake_minimum_required(VERSION 3.0.2)
project(topic_monitor)
find_package(catkin REQUIRED)

catkin_python_setup()
catkin_package()

catkin_install_python(PROGRAMS src//topic_monitor/exec/topic_monitor_ros1
                      DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})

# if (CATKIN_ENABLE_TESTING)
#  find_package(rostest REQUIRED)
# endif()
