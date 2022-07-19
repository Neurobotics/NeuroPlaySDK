/// @description Fetch NeuroPlayPro response


if ds_map_find_value(async_load, "id") == get  // General check for request 
{
    if ds_map_find_value(async_load, "status") == 0 // General check for request's status
    {
        response = ds_map_find_value(async_load, "result"); // General result fetch
		show_debug_message(response);
		json = json_parse(response);

		// If response has meditation - update this object's variable "meditation" value
		if variable_struct_exists(json, "meditation")
		{
			meditation = json.meditation;
		}
    }
    else
    {
        response = "null";
    }
}

