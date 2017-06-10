from lapsetime import TimeSpans

timespans = TimeSpans()

# uncomment and modify if you want to override default threading preferences.
# cpu_count = 4


outside = dict(
    name="Outside 1",
    sequence_storage=r'F:\Timelapse\Image Sequences\Outside 1',
    inputdir=r'F:\Timelapse\2016\Outside 1',
    exports=dict(
        full=dict(
            subdir=r'Full',
            minutelist=[0],
            span='Full Time Span 15 Minute Intervals - Outside',
            drawtimestamp=True,
            optimize=True,
            prefix="Outside ",
            enabled=True
        ),
        all=dict(
            subdir=r'All Frames',
            allframes=True,
            span='Every Frame - Outside',
            drawtimestamp=True,
            optimize=True,
            prefix="Outside ",
            enabled=False
        ),
        day=dict(
            subdir=r'Day',
            hourlist=[i for i in xrange(5, 22)],
            minutelist=timespans.fifteenminutes,
            span='Day Time Only 5am to 9pm - 15 minute intervals - Outside',
            drawtimestamp=True,
            optimize=True,
            prefix="Outside ",
            enabled=True
        ),
        night=dict(
            subdir=r'Night',
            hourlist=timespans.night,
            minutelist=timespans.fifteenminutes,
            span='Night Time Only 9pm to 5 am - 15 minute intervals - Outside',
            drawtimestamp=True,
            optimize=True,
            prefix="Outside ",
            enabled=True
        ),
    )
)

# Seed Closet
seed_closet = dict(
    name="Seed Closet",
    sequence_storage=r'F:\Timelapse\Image Sequences\Seed Closet',
    inputdir=r'F:\Timelapse\2016\Seedling Closet',
    exports=dict(
        full=dict(
            subdir=r'Full',
            minutelist=[0],
            span='Full Time Span 15 Minute Intervals - Seed Closet',
            drawtimestamp=True,
            optimize=True,
            prefix="Seed Closet ",
            enabled=True
        ),
        all=dict(
            subdir=r'All Frames',
            allframes=True,
            span='Every Frame - Seed Closet',
            drawtimestamp=True,
            optimize=True,
            prefix="Seed Closet ",
            enabled=False
        ),
        day=dict(
            subdir=r'Day',
            hourlist=[i for i in xrange(5, 22)],
            minutelist=timespans.fifteenminutes,
            span='Day Time Only 5am to 9pm - Seed Closet',
            drawtimestamp=True,
            optimize=True,
            prefix="Seed Closet ",
            enabled=True
        ),
        night=dict(
            subdir=r'Night',
            hourlist=timespans.night,
            minutelist=timespans.fifteenminutes,
            span='Night Time Only 9pm to 5 am - Seed Closet',
            drawtimestamp=True,
            optimize=True,
            prefix="Seed Closet ",
            enabled=True
        ),
    )
)
