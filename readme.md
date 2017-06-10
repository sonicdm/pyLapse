# pyLapse
Automatically save images from ip cameras into collections for export and or render
detailed scheduling and export options

## Current Functionality
The core of pyLapse lies in the ImgSeq module. This is where all of the image capturing, saving, filtering and processing happens.
Still very much WIP

### Image loading, filtering and saving
#### Load a directory of files:
```python
from pyLapse.ImgSeq.collections import Collection
collection = Collection('Name', r'output_directory_goes_here', r'input_directory_goes here',)
>>> print collection
Image Collection: Name, Location: Input Directory, Image Count: 12020
```

#### Configure an export:
```python
# Creates an export that exports every 15 minutes of every other hour.
# Follows traditional cron formats. 
# subdir is the location inside the export directory to write to if specified. 
collection.add_export('Export Name', subdir='subdirectory', minute='*/15', hour='*/2')
```
#### Run an export:
```python
# Runs the export and passes on arguments to the image writer
collection.export.run('Export Name', '/path/to/output/', drawtimestamp=True, optimize=True)
```

## Planned Web Interface Outline:
### MENU
* Home - /
  * Captures - /captures
  * Cameras - /cameras
  * Collections - /collections
  * Time Ranges - /timefilters
  * Scheduler - /scheduler
  * Import/Export ->
     * Import /collections/import
     * Export - /export
 * Logs - /logs


### Endpoint Map
```/
    Dashboard
        List of scheduled captures - link to edit captures:
            per line
                pause/resume button
                details: Caputure name, Cameras Used, Last capture, Next capture, Total frames, size on disk
                edit/delete links - /captures
                force download
        Camera Previews (optional):
            1 up, 2 up, 4 up, Etc..
        Collections:
            Last captured images
        Storage Stats
        Notifications (missed captures, drive space running low, capture ended/started etc., 
                       empty capture detected)


/settings - ini file not db.
    /general
        Web Server
            port
            ip
            https?
            https port

        Security
            allow outside access?
        Options
            Launch browser on startup?: []
        [Save Changes] [Restart pyLapse]

    /cameras
        [Add Camera]
        List of cameras:
            per line
                Camera Name, Status, enabled [], edit link, delete link
            /manage
                /add
                    name
                    full res shot url: Url for the full size image. ex: http://192.168.1.100:8080/photoaf.jpg
                    ## used for the live preview
                    video still url: If different from full res. ex: http://192.168.1.100:8080/shot.jpg
                    video feed: (Not sure if I am gonna do this but just in case)
                    username: (optional)
                    password: (optional)
                    enabled?: []
                    [Save] [Save & Add New]
                /remove
                /edit
                    fields from /add
                    [save] [remove]

    /notifications
        idk i guess people use this

    /advanced


/timefilters - set up ranges
    /add
        name
        date span: (selected, single, all, range) Calendar widget? (default to all)
        hours: (checkboxes? multiselect list?)
        minutes: (checkboxes? multiselect list?)
        [Save] [Save & Add New]
    /remove
    /edit


/captures
    /add
        Name
        Destination collection(s?): Dropdown list/multi list - link to create new collection
        Cameras: (multi select list of added camera feeds) add camera link?
            camera alias: short name alias for camera in file names
        Start: Date/Time to begin the capture
        End: Date/Time to end the capture
        Capture interval: (seconds, minutes, hours, days) gotta figure out a clean way to do this..
        Active Times Range: ex: from 7:45am to 8:15pm
        [Save] [Save & Add New]
    /remove
    /edit


/collections
    /import
        import from folder
            source folder
            import to existing collection?: [] (default no) ->
                choose collection: dropdown list?
                copy or move files?: dropdown list?
            name: Collection Name
            source filename mask: regex, strptime, or image seq
            destination filename mask: strftime & tags (default '<prefix> - <camera> - yyyy-mm-dd-hhmmss')
            collection folder location: (default: %user%/pictures/pyLapse/<collection name>)
            Auto resize?; [] (default no) ->
                size: default (1920x1080)
                quality: (default 50)
                always?: [] always resize on add or just this once (default just this once)
            [import] [preview import?]
    /add
        name: Collection Name
        prefix: filename prefix for collection
        destination filename mask: strftime & tags (default '<prefix> - <camera alias> - yyyy-mm-dd-hhmmss')
        auto-resize?: [] Automatically resize images added to collection (default off)
            size: default (1920x1080)
            quality: (default 50)
        collection folder location: (default: %user%/pictures/pyLapse/<collection name>)
    /delete
    /edit
    /scenes?
    /clips: exported files? 



/export
    Presets: dropdown list?
    Collection: select a collection (default to linked from collection)
        select camera
    Timeframe Preset: select a timeframe preset (default to everything) - /timefilters
        link to add new preset here?
    Timeframe Selection: - one time or populated from /timefilters selected preset - default to ALL FRAMES
        or add preset this way?
        Save as preset? []
        Preset name
    Export type: dropdown? type of export (image sequence, video, zip, ???)
        Image Sequence: options for image sequence export
            prefix: text to prefix before sequence (default: none)
            digit width:

    Destination File/Folder: output folder/filename
    Save as preset? []
    Preset Name

    /imagesequence
    /video
    /presets


/scheduler
    /add
        task (export, clear export targets, render)
        time
    /remove
    /edit


/logs - display logs```
