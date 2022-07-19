/// @description Display meditation results

draw_set_colour(c_lime);
draw_text(50,10,"Meditation: " + string(meditation) + "%"); //Display current meditation

draw_set_colour(c_white);
resp = string_replace_all(response, ",", ", ") // Add line breaks
draw_text_ext(50,100, resp, 30, 50);
