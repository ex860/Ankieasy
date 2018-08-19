
def GetCardType(models):
    return "Japanese (recognition&recall)"

def MakeCard(data):
    result = {}

    if 'front_word' not in data and 'back_word' not in data or 'read_word' not in data:
        return result
    result['Expression'] = data['front_word']
    result['Meaning'] = data['back_word']
    result['Reading'] = data['read_word']
    return result
