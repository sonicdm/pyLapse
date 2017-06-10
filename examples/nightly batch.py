"""
Example file of a batch to run many collection exports at once.
"""
from pyLapse.ImgSeq.collections import Collection
from datetime import datetime

start = datetime.now()

writer_args = dict(drawtimestamp=True, resize=True)

outside = Collection('Outside',
                     r'F:\Timelapse\Image Sequences\Outside 1',
                     r'F:\Timelapse\2016\Outside 1')

seed_closet = Collection('Seed Closet',
                         r'F:\Timelapse\Image Sequences\Seed Closet',
                         r'F:\Timelapse\2016\Seedling Closet')

seed_closet.add_export('Full', 'Full', 'Seed Closet Full ', 'Seedling All Day', hour='*', minute='0')
seed_closet.add_export('Day', 'Day', 'Seed Closet Day ', 'Seedling Daytime only', hour='5-23', minute='*/30')
seed_closet.add_export('Night', 'Night', 'Seed Closet Night ', 'Seedling nighttime only', hour='23,0-5', minute='*/10')
seed_closet.add_export('Noon', 'Noon', 'Seed Closet Noon ', 'Seedling 1 per day @ Noon', hour='12', minute='0')

outside.add_export('Full', 'Full', 'Outside Full ', 'Outside All Day', hour='*', minute='0')
outside.add_export('Day', 'Day', 'Outside Day ', 'Outside Daytime only', hour='5-23', minute='*/30')
outside.add_export('Night', 'Night', 'Outside Day ', 'Outside nighttime only', hour='5-23', minute='*/10')
outside.add_export('Noon', 'Noon', 'Outside Noon ', 'Outside 1 per day @ Noon', hour='12', minute='0')


def main():
    print "-------------------------------------\n" \
          "Running Nightly Image Sequence Batch:\n" \
          "Started at: {start}\n" \
          "-------------------------------------".format(start=start)
    print "----------------\n%s\n" \
          "----------------" % seed_closet
    seed_closet.export_all(**writer_args)
    print "----------------\n%s" % outside
    outside.export_all(**writer_args)
    end = datetime.now()
    print "-------------------------------------\n" \
          "Nightly Batch Completed at {end}\n" \
          "Duration: {duration}\n" \
          "-------------------------------------".format(end=end, duration=end - start)


if __name__ == '__main__':
    main()
