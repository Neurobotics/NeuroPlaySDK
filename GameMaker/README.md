# Опрос NeuroPlayPro в GameMaker

1. Создайте пустой Объект (Object), назовите его «neuroplay_timer» и добавьте его на сцену 

2. В панели Событий (Events) создайте события типа `Create`, Alarm/`Alarm0`, Asynchronous/`Async – HTTP`

3. В событии `Create` для взвода таймера напишите:

```
alarm_set(0, room_speed);
```


4. В событии `Alarm0`:

```
get = http_get("http://127.0.0.1:2336/bci");
alarm_set(0, room_speed)
```

5. В событии `Async - HTTP`:

```
if ds_map_find_value(async_load, "id") == get  
{
    if ds_map_find_value(async_load, "status") == 0 
    {
        response = ds_map_find_value(async_load, "result");
        json = json_parse(response);
        if variable_struct_exists(json, "meditation")
        {
           meditation = json.meditation;
        }
    } 
}
```

# How to query NeuroPlayPro in GameMaker

1. Create an empty Object, entitle it "neuroplay_timer" and add to the scene 

2. In the Events tab of "neuroplay_timer" add events of types: `Create`, Alarm/`Alarm0`, Asynchronous/`Async – HTTP`

3. In the code of the `Create` event add the following code (to start the timer):

```
alarm_set(0, room_speed);
```

4. In the `Alarm0` event:
```
get = http_get("http://127.0.0.1:2336/bci"); 
alarm_set(0, room_speed)
```

5. In the `Async - HTTP` event:
```
if ds_map_find_value(async_load, "id") == get  
{
    if ds_map_find_value(async_load, "status") == 0 
    {
        response = ds_map_find_value(async_load, "result");
        json = json_parse(response);
        if variable_struct_exists(json, "meditation")
        {
           meditation = json.meditation;
        }
    } 
}
```
