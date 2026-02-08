"""Example: batch-run multiple collection exports at once.

Update the paths below to match your setup before running.
"""
from __future__ import annotations

from datetime import datetime

from pyLapse.img_seq.collections import Collection

start = datetime.now()

writer_args: dict = dict(drawtimestamp=True, resize=True)

# -- Configure your collections (update paths) ----------------------------

outside = Collection(
    "Outside",
    r"F:\Timelapse\Image Sequences\Outside 1",  # export_dir
    r"F:\Timelapse\2016\Outside 1",  # source collection_dir
)

seed_closet = Collection(
    "Seed Closet",
    r"F:\Timelapse\Image Sequences\Seed Closet",
    r"F:\Timelapse\2016\Seedling Closet",
)

# -- Define export presets -------------------------------------------------

seed_closet.add_export("Full", "Full", "Seed Closet Full ", "All Day", hour="*", minute="0")
seed_closet.add_export("Day", "Day", "Seed Closet Day ", "Daytime only", hour="5-23", minute="*/30")
seed_closet.add_export("Night", "Night", "Seed Closet Night ", "Nighttime only", hour="23,0-5", minute="*/10")
seed_closet.add_export("Noon", "Noon", "Seed Closet Noon ", "1 per day @ Noon", hour="12", minute="0")

outside.add_export("Full", "Full", "Outside Full ", "All Day", hour="*", minute="0")
outside.add_export("Day", "Day", "Outside Day ", "Daytime only", hour="5-23", minute="*/30")
outside.add_export("Night", "Night", "Outside Night ", "Nighttime only", hour="23,0-5", minute="*/10")
outside.add_export("Noon", "Noon", "Outside Noon ", "1 per day @ Noon", hour="12", minute="0")


def main() -> None:
    print(
        f"-------------------------------------\n"
        f"Running Nightly Image Sequence Batch:\n"
        f"Started at: {start}\n"
        f"-------------------------------------"
    )
    print(f"----------------\n{seed_closet}\n----------------")
    seed_closet.export_all(**writer_args)

    print(f"----------------\n{outside}\n----------------")
    outside.export_all(**writer_args)

    end = datetime.now()
    print(
        f"-------------------------------------\n"
        f"Nightly Batch Completed at {end}\n"
        f"Duration: {end - start}\n"
        f"-------------------------------------"
    )


if __name__ == "__main__":
    main()
