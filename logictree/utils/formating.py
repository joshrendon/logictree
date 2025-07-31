def indent(text, spaces):
    pad = " " * spaces
    return "\n".join(pad + line for line in text.splitlines())
