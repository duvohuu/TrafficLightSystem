include("${CMAKE_CURRENT_LIST_DIR}/rule.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/file.cmake")

set(Code_default_library_list )

# Handle files with suffix (s|as|asm|AS|ASM|As|aS|Asm), for group default-XC8
if(Code_default_default_XC8_FILE_TYPE_assemble)
add_library(Code_default_default_XC8_assemble OBJECT ${Code_default_default_XC8_FILE_TYPE_assemble})
    Code_default_default_XC8_assemble_rule(Code_default_default_XC8_assemble)
    list(APPEND Code_default_library_list "$<TARGET_OBJECTS:Code_default_default_XC8_assemble>")
endif()

# Handle files with suffix S, for group default-XC8
if(Code_default_default_XC8_FILE_TYPE_assemblePreprocess)
add_library(Code_default_default_XC8_assemblePreprocess OBJECT ${Code_default_default_XC8_FILE_TYPE_assemblePreprocess})
    Code_default_default_XC8_assemblePreprocess_rule(Code_default_default_XC8_assemblePreprocess)
    list(APPEND Code_default_library_list "$<TARGET_OBJECTS:Code_default_default_XC8_assemblePreprocess>")
endif()

# Handle files with suffix [cC], for group default-XC8
if(Code_default_default_XC8_FILE_TYPE_compile)
add_library(Code_default_default_XC8_compile OBJECT ${Code_default_default_XC8_FILE_TYPE_compile})
    Code_default_default_XC8_compile_rule(Code_default_default_XC8_compile)
    list(APPEND Code_default_library_list "$<TARGET_OBJECTS:Code_default_default_XC8_compile>")
endif()

add_executable(${Code_default_image_name} ${Code_default_library_list})

target_link_libraries(${Code_default_image_name} PRIVATE ${Code_default_default_XC8_FILE_TYPE_link})

# Add the link options from the rule file.
Code_default_link_rule(${Code_default_image_name})


# Post build target to copy built file to the output directory.
add_custom_command(TARGET ${Code_default_image_name} POST_BUILD
                    COMMAND ${CMAKE_COMMAND} -E make_directory ${Code_default_output_dir}
                    COMMAND ${CMAKE_COMMAND} -E copy ${Code_default_image_name} ${Code_default_output_dir}/${Code_default_original_image_name}
                    BYPRODUCTS ${Code_default_output_dir}/${Code_default_original_image_name})
