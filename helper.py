import datetime


def diffformat(total_seconds=None):
    """ convert seconds to custom minutes and seconds object """
    if total_seconds:
        minutes = int(total_seconds // 60)
        seconds = int(total_seconds % 60)
    else:
        minutes = "0"
        seconds = "0"

    print("diffformat helper: total seconds: {} minutes: {} seconds: {}".format(total_seconds, minutes, seconds))

    return type('difftime', (object,), {'minutes': minutes,
                                        'seconds': seconds})  # create inline object https://stackoverflow.com/questions/1528932/how-to-create-inline-objects-with-properties-in-python


def write_to_file(string, extension="html"):
    """ write data to file with today's date
    example: _2019-07-02 17:46:58.html """
    file_name = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("_{}.{}".format(file_name, extension), "w+") as data_file:
        data_file.write(string)
