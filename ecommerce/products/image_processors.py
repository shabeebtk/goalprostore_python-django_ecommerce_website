from imagekit.processors import ResizeToFill


class Square_Thumbnail(ResizeToFill):
    width = 300
    height = 300
    
class Sixteen_Nine_Thumbnail(ResizeToFill):
    width = 1600
    height = 900

class Banner_Thumbnail(ResizeToFill):
    width = 1200
    height = 400