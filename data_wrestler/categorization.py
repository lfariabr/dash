# Função para categorizar com base nas palavras-chave
def categorize(text):
    for keyword, category in category_mapping.items():
        if pd.notna(text) and keyword.lower() in text.lower():
            return category
    return 'Indefinido'