"""
good
"""

def write_synonyms(synonyms):
    """
    write_synonyms
    """
    file = open('synonyms.txt', 'w')
    for i, j in synonyms.items():
        string = ''
        file.write(i + ':{')
        for word in list(j):
            string += word + ', '
        file.write(string[:-2]+'}\n')
    file.close()

def get_consts():
    """
    write_synonyms
    """
    noun_endings = {"а", "о", "и", "у", "ы", "ик"}

    letters = set("кнгшщзьблдфвпрснчмтжъхзй")

    adjective_endings = {"ый", "ий", "ым", "ой", "ая", "ую", "ое", "ее", "го", "ые"}

    return noun_endings, letters, adjective_endings

def add_synonym_to_file(string):
    """
    write_synonyms
    """
    file = open('buffer.txt', 'w')
    file.write(string)
    file.close()


def update_synonyms(string, synonyms):
    """
    write_synonyms
    """
    try:
        file = open('buffer.txt', 'r')
    except IOError:
        return

    synonym = file.readline()
    if synonym == 'gg\n':
        return

    if not cmp(synonym, string):
        return

    if synonyms.get(string) is None:
        synonyms[string] = {synonym}
    else:
        synonyms[string].add(synonym)
    file.close()

def get_set(string):
    """
    write_synonyms
    """
    string = set(string[string.find('{') + 1: string.find('}')].split(', '))
    return string

def get_synonyms():
    """
    write_synonyms
    """
    try:
        file = open("synonyms.txt", 'r')
    except IOError:
        return dict()
    synonyms = dict()
    for i in file:
        synonyms[i[:i.find(':')]] = get_set(i)
    file.close()

    return synonyms

def cmp(string1, string2):
    """
    write_synonyms
    """
    alen = len(string1)
    blen = len(string2)
    recur = [[(i+j) if i*j == 0 else 0 for j in range(blen + 1)] for i in range(alen + 1)]

    for i in range(1, alen + 1):
        for j in range(1, blen + 1):
            if string1[i-1] == string2[j-1]:
                recur[i][j] = recur[i-1][j-1]
            else:
                recur[i][j] = 1 + min(recur[i-1][j], recur[i-1][j-1], recur[i][j-1])
    return (recur[alen][blen] / max(alen, blen)) < 0.5

def find_category(string, base):
    """
    write_synonyms
    """
    def delete_endings(string):
        for i in ('"', ",", '%', ':', '.'):
            string = string.replace(i, '')
        result = ''
        for i in string.split():
            if i[-2:] in adjective_endings:
                result += i[:-2] + ' '
            elif i[-1:] in noun_endings:
                result += i[:-1] + ' '
            else:
                result += i + ' '

        return result[:-1]


    def get_noun(string):
        """
        write_synonyms
        """
        for i in string.split():
            if i[-1:] in noun_endings:
                return i
            if i[-2:] in adjective_endings:
                return ''
            if i[-1:] in letters:
                return i

        return ''

    def replace_with_synonym(noun):
        """
        write_synonyms
        """
        noun = delete_endings(noun)
        for i, j in synonyms.items():
            if (i == noun) or (noun in j):
                return i
        return noun

    def get_adjective(string):
        """
        write_synonyms
        """
        for i in string.split():
            if i[-2:] in adjective_endings:
                return i
        return ''

    def get_category(string, noun, synonyms):
        """
        write_synonyms
        """
        result = None
        clarifications = []
        if len(string.split()) == 1:
            string = ''

        noun1 = delete_endings(noun)

        noun = replace_with_synonym(noun)
        string = delete_endings(string).replace(noun1, noun)
        for i, category in base.items():
            good_category = delete_endings(category.lower())
            if noun in good_category.split():
                if string == '':
                    clarifications.append(category)
                    result = i
                else:
                    flag = True
                    for j in string.split():
                        if j not in good_category:
                            flag = False
                    if flag:
                        clarifications.append(category)
                        result = i


        quan = len(clarifications)
        if quan <= 0:
            add_synonym_to_file(noun)
            return (quan, None)
        update_synonyms(noun, synonyms)
        add_synonym_to_file('gg\n')
        return (quan, result if quan == 1 else clarifications)

    synonyms = get_synonyms()

    noun_endings, letters, adjective_endings = get_consts()

    string = string.lower()

    noun = get_noun(string)
    if noun == '':
        adj = get_adjective(string)
        if adj == '':
            return (0, None)

        result = get_category(string, adj, synonyms)
        write_synonyms(synonyms)
        return result


    result = get_category(string, noun, synonyms)
    write_synonyms(synonyms)
    return result
