#!/usr/bin/python3
import re
import random
import pymorphy2
import json
import emotions
from plumbum import cli

morph = pymorphy2.MorphAnalyzer()

codes = {
    'n': 'nomn',
    'g': 'gent',
    'd': 'datv',
    'ac': 'accs',
    'a': 'ablt',
    'l': 'loct'
}

keywords = set(open('keywords.txt').read().replace(' ', '').split('\n'))
arguments = json.load(open('arguments.json'))
random.shuffle(arguments)

shuffled = set()


def mychoise(lst):
    kek = lst.pop(0)
    lst.append(kek)
    return random.choice(lst)


def to_padez(val, padez):
    if padez in codes:
        padez = codes[padez]
    return morph.parse(val)[0].inflect({padez}).word


def getwordlist(s):
    clear_text = re.sub("[^а-яА-Я]",
                        " ",  # The pattern to replace it with
                        s)
    s = s[0].lower() + s[1:]
    local_words = clear_text.split()
    return local_words


class EssayBuilder:
    def __init__(self, raw_text):
        self.text = raw_text.split('\n')
        self.author = self.text[-1]
        self.text = "".join(self.text[:-1])

        self.text_tokens = list(map(lambda s: s[1:] if s[0] == ' ' else s,
                                    filter(lambda a: len(a) > 4, re.split("\.|\?|!|;", self.text))))

        words = {}
        for i, s in zip(range(10 ** 9), self.text_tokens):
            local_words = getwordlist(s)
            words_cnt = {}
            for w in local_words:
                p = morph.parse(w)
                j = 0
                while len(p) > 0 and 'NOUN' not in p[0].tag and j < 1:
                    p = p[1:]
                    j += 1
                if len(p) > 0 and 'NOUN' in p[0].tag:
                    w = p[0].normal_form
                    if w not in words_cnt:
                        words_cnt[w] = 0
                    words_cnt[w] += 1

            for w in words_cnt:
                if w not in words:
                    words[w] = {
                        'total': 0,
                        'sent': []
                    }
                words[w]['total'] += words_cnt[w]
                words[w]['sent'].append((i, words_cnt[w]))
        self.all_words = sorted([{'word': w,
                                  'total': val['total'],
                                  'sent': sorted(val['sent'], key=lambda a: a[1])} for w, val in
                                 words.items()], key=lambda a: -a['total'])

        self.good_words = list(filter(lambda a: a['word'] in keywords, self.all_words))

        self.samples = json.load(open('awesome_text.json'))
        self.samples['baseword'] = [self.good_words[0]['word']]

        for s in self.samples:
            random.shuffle(self.samples[s])

    def get_str(self, val):
        if val == "author":
            if random.randint(0, 4) == 0: return self.author
        vals = val.split('_')
        self.samples[vals[0]] = self.samples[vals[0]][1:] + [self.samples[vals[0]][0]]
        ret = self.samples[vals[0]][-1]
        if len(vals) > 1:
            if vals[1] in codes:
                vals[1] = codes[vals[1]]
            ret = morph.parse(ret)[0].inflect({vals[1]}).word
        return ret

    def get_problem(self):
        return ['#intro',
                "#wholeproblem"]

    def get_quatation_comment(self):
        w = mychoise(self.good_words)
        s = self.text_tokens[mychoise(w['sent'])[0]]
        comment = ["#commentbegin, #author в словах \"%s\" #speaks о %s" % \
                   (s, to_padez(w['word'], 'loct'))]
        return comment

    def get_epitet(self):
        noun = []
        w = None
        while len(noun) < 2:
            noun = []
            w = mychoise(self.good_words)
            s = self.text_tokens[mychoise(w['sent'])[0]]
            for _ in getwordlist(s):
                word = morph.parse(_)[0]
                if w['word'] != word.normal_form and 'NOUN' in word.tag:
                    noun.append(word.normal_form)

        comment = ["показывая важность понятия \"%s\", #author оперирует понятиями %s и %s" % \
                   (w['word'], to_padez(noun[0], 'g'), to_padez(noun[1], 'g'))]
        return comment

    def get_comment(self):
        comment_sources = [self.get_quatation_comment, self.get_epitet]
        comment = []
        for i in range(3):
            comment.extend(mychoise(comment_sources)())
        return comment

    def get_author_position(self):
        return ["позиция #author_g в этом фрагменте лучше всего выраженна цитатой: \"%s\"" %
                (random.choice(self.text_tokens))]

    def get_my_position(self):
        return ["#myposition"]

    def get_lit_argument(self):
        curbook = mychoise(arguments)
        curarg = mychoise(curbook['args'])
        replacements = {
            'author': curbook['author'],
            'book': curbook['book'],
            'hero': curarg['hero'],
            'action': random.choice(curarg['actions'])
        }
        if curbook['native']:
            replacements['native'] = 'отечественной '
        else:
            replacements['native'] = ''

        return ["в %(native)sлитературе много примеров #baseword_g" % replacements,
                "#example, в романе %(book)s, который написал %(author)s,"
                " герой по имени %(hero)s %(action)s, показывая таким образом своё отношение к #baseword_d" % replacements]

    def get_left_argument(self):
        pass

    def get_conclusion(self):
        return ["#conclude0 #many в жизни зависит от #baseword_g",
                "Необходимо всегда помнить о важности этого понятия в нашей жизни"]

    def build_essay(self):
        abzaces = [self.get_problem(), self.get_comment(), self.get_author_position(),
                   self.get_my_position(), self.get_lit_argument(), self.get_conclusion()]
        nonterm = re.compile('#[a-z0-9_]+')
        str_out_all = ''
        for a in abzaces:
            str_out = ''
            for s in a:
                while re.search(nonterm, s) is not None:
                    val = re.search(nonterm, s).group()[1:]
                    if val.split('_')[0] in self.samples:
                        s = s.replace('#' + val, self.get_str(val))
                    else:
                        s = s.replace('#' + val, '%' + val)

                str_out += s[0].upper() + s[1:] + '. '
            str_out += '\n'
            str_out_all += str_out
        return str_out_all


from sys import stdin, stdout


class MyApp(cli.Application):
    _abuse = 0
    _output = ''

    @cli.switch(['-e'], float, help='Change emotionality')
    def abuse_lexical(self, abuse):
        self._abuse = abuse

    @cli.switch(['-o'], str, help='Output')
    def output(self, output):
        self._output = output


    def main(self, filename='text-tokareva.txt'):
        raw_text = open('text-tokareva.txt', 'r').read()
        if self._output=='':
            self._output=filename+'.out'
        out = open(self._output, 'w')
        e = EssayBuilder(raw_text)
        str_out = e.build_essay()
        str_out = emotions.process(str_out, self._abuse)
        out.write(str_out)


if __name__ == '__main__':
    MyApp.run()
