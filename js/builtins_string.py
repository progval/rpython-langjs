def char_at(this, *args):
    string = this.ToString()
    if len(args)>=1:
        pos = args[0].ToInt32()
        if (not pos >=0) or (pos > len(string) - 1):
            return ''
    else:
        return ''
    return string[pos]
