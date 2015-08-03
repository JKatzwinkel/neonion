from common.uri import generate_uri
from exceptions import NoConceptAnnotationError


def add_resource_uri(annotation):
    if 'rdf' in annotation:
        if 'uri' not in annotation['rdf']:
            uri = generate_uri(annotation['rdf']['typeof'], annotation['quote'])
            if uri is not None:
                annotation['rdf']['uri'] = uri
    else:
        raise NoConceptAnnotationError(annotation)

    return annotation
