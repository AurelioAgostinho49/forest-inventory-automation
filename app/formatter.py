def formatar_nome_comum(nome):
    if not nome:
        return nome
    return nome.title()


def formatar_nome_cientifico(nome):
    if not nome:
        return nome

    partes = nome.split()

    if len(partes) >= 2:
        return partes[0].capitalize() + " " + " ".join(p.lower() for p in partes[1:])
    
    return nome.capitalize()