cmake_minimum_required(VERSION 3.5.0 FATAL_ERROR)


set(CPM_MODULE_NAME firmware_tools)

#-----------------------------------------------------------------------
# Required CPM Setup - no need to modify - See: https://github.com/iauns/cpm
#-----------------------------------------------------------------------
set(CPM_LIB_TARGET_NAME ${CPM_MODULE_NAME})

if ((DEFINED CPM_DIR) AND (DEFINED CPM_UNIQUE_ID) AND (DEFINED CPM_TARGET_NAME))
    set(CPM_LIB_TARGET_NAME ${CPM_TARGET_NAME})
    set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} ${CPM_DIR})
    include(CPM)
else()
    set (CPM_DIR "${CMAKE_CURRENT_BINARY_DIR}/cpm-packages" CACHE TYPE STRING)
    find_package(Git)
    if(NOT GIT_FOUND)
        message(FATAL_ERROR "CPM requires Git.")
    endif()
    if (NOT EXISTS ${CPM_DIR}/CPM.cmake)
        message(STATUS "Cloning repo (https://github.com/iauns/cpm)")
        execute_process(
            COMMAND "${GIT_EXECUTABLE}" clone https://github.com/iauns/cpm ${CPM_DIR}
            RESULT_VARIABLE error_code
            OUTPUT_QUIET ERROR_QUIET)
        if(error_code)
            message(FATAL_ERROR "CPM failed to get the hash for HEAD")
        endif()
    endif()
    include(${CPM_DIR}/CPM.cmake)
endif()

CPM_InitModule(${CPM_MODULE_NAME})

#-----------------------------------------------------------------------
# Required variables: these should be supplied by the parent CMakeLists
#-----------------------------------------------------------------------
#
# FW_UPDATE_CFG_FILE        path to config file   (e.g. /path/upload.cfg)
#-----------------------------------------------------------------------
# Project sources / settings
#-----------------------------------------------------------------------

set(MODULE_DIR "${CMAKE_CURRENT_LIST_DIR}/${CPM_MODULE_NAME}")
set(UPDATE_SCRIPT "${MODULE_DIR}/firmware_update.py")

if(NOT TARGET update)
    add_custom_target(update
        COMMAND ${UPDATE_SCRIPT} --config ${FW_UPDATE_CFG_FILE}
    )
endif(NOT TARGET update)

