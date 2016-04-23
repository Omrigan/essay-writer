mat = [
    'сука', "блять", "пиздец", "нахуй", "твою мать", "епта"]
import random
import re

# strong_emotions = re.sub('[^а-я]', ' ', open('strong_emotions').read().lower()).split()


def process(txt, ch):
    words = txt.split(" ")
    nxt = words[0] + ' '
    i = 1
    while i < len(words) - 1:

        if words[i - 1][-1] != '.' and random.random() < ch:
            nxt += random.choice(mat) + " "
        else:
            nxt += words[i] + " "
            i += 1
    nxt += words[-1]
    return nxt
