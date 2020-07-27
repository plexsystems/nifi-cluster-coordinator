from bar import utils


def is_true():
    """This is always true."""
    return True


if __name__ == '__main__':
    if is_true():
        print("This is true")

    if utils.is_false():
        print("The universe is wrong!!!!")
