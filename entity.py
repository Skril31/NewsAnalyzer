import sqlite3
from natasha import (
    MorphVocab,
    NewsEmbedding,
    Doc,
    Segmenter,
    NewsMorphTagger,
    NewsSyntaxParser,
    NewsNERTagger,
    PER,
    LOC,
    ORG,
    NamesExtractor
)

# Создание экземпляров Natasha
segmenter = Segmenter()
morph_vocab = MorphVocab()
emb = NewsEmbedding()
morph_tagger = NewsMorphTagger(emb)
syntax_parser = NewsSyntaxParser(emb)
ner_tagger = NewsNERTagger(emb)
names_extractor = NamesExtractor(morph_vocab)


def names_entity(texts):
    # Обработка каждого текста
    for text in texts:
        text = text[0]
        doc = Doc(text)

        doc.segment(segmenter)
        doc.tag_morph(morph_tagger)
        doc.parse_syntax(syntax_parser)
        doc.tag_ner(ner_tagger)

        # Извлечение и добавление сущностей в таблицу entity
        entities = []
        for span in doc.spans:
            if span.type in [PER, ORG, LOC]:
                span.normalize(morph_vocab)
                if span.normal not in entities and span.normal not in ["Волгоград", "РФ", "Россия", "Волгоградская область", "ВОЛГОГРАД", "ТАСС"]:
                    entities.append(span.normal)
        name_entities = ', '.join(entities)

        # Обновление столбца name_entity
        with sqlite3.connect("news.db") as con:
            cursor = con.cursor()
            cursor.execute("UPDATE news SET name_entity = ? WHERE content = ?", (name_entities, text))
