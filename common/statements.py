from exceptions import NoSemanticAnnotationError

DEFAULT_PREFIXES = '''PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd:<http://www.w3.org/2001/XMLSchema#>
PREFIX owl:<http://www.w3.org/2002/07/owl#>
PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX sesame:<http://www.openrdf.org/schema/sesame#>
PREFIX fn:<http://www.w3.org/2005/xpath-functions#>
'''


def general_statement(annotation):
    if 'rdf' in annotation:
        rdf = annotation['rdf']

        # add prefixes and insert preamble
        query = DEFAULT_PREFIXES + u'\nINSERT DATA {'
        # add type property
        query += u'\n<{}> rdf:type <{}>;'.format(rdf['uri'], rdf['typeof'])
        # add label property
        query += u'\nrdfs:label "{}";'.format(rdf['label'])

        if 'sameAs' in rdf:
            # add sameAs relation
            query += u'\nowl:sameAs <{}>;'.format(rdf['sameAs'])

        # add end of statement
        query += u'.\n}'

        #print(query)
        return query
    else:
        raise NoSemanticAnnotationError(annotation)