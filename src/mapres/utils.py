from .resolver import res

def rprint(text: str, **ctx) -> None:
    '''Simple global resolution and print'''
    print(res(text, **ctx))