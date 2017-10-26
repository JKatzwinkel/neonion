from client import WikidataClient

from django.utils import timezone

from annotationsets.models import LinkedConcept, LinkedProperty, PropertyConceptOccurrence, Concept, Property, ConceptSet

template = """
    select distinct ?sub ?subLabel ?property ?propertyLabel ?type ?typeLabel ?obj ?objLabel {{
      {{
        ?sub ?p wd:{entity} .
        ?sub wdt:P31 ?type .
        ?property wikibase:directClaim ?p .
        SERVICE wikibase:label {{
          bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en"
        }}
      }} union {{
        wd:{entity} ?p ?obj .
        ?obj wdt:P31 ?type .
        ?property wikibase:directClaim ?p .
        SERVICE wikibase:label {{
          bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en"
        }}
      }}
    }}"""

templ_super = """
  select distinct ?superclass ?superclassLabel {{
    wd:{entity} wdt:P279 ?superclass .
    SERVICE wikibase:label {{
      bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en".
    }}
  }}"""


get = lambda record, key: record.get(key, {}).get('value')

class TestRecommender(object):

    wiki = WikidataClient()



    def common_superclass(self, entities):


      concepts = {e: [] for e in entities}
      for i in range(2):
        for entity in [e for e, k in concepts.items() if len(k) < 1]:
          res = self.wiki.sparql(templ_super.format(entity=self.wiki.extract_id(entity)))
          for fact in res:
            self.labels[get(fact, 'superclass')] = get(fact, 'superclassLabel')
          if len(res) > 0:
            concepts[entity] = [get(r, 'superclass') for r in res]
            for concept in concepts[entity]:
              concepts[concept] = []
          else:
            concepts.pop(entity)

      # graph assembly done
      # now walk up tree
      visits = {e:entities.count(e) for e in entities}
      frontier = entities[:]
      while len(frontier) > 0:
        for entity in frontier[:]:
          # perform step from concept to superclass
          frontier.remove(entity)
          frontier.extend(concepts.get(entity, []))
          for c in concepts.get(entity, []):
            visits[c] = visits.get(c, 0) + 1
      # return betweenness values
      return visits



    def entity_rec(self, entity_id):

        query = template.format(entity=entity_id)

        res = self.wiki.sparql(query)

        properties = {}
        types = {}
        self.labels = {}


        for fact in res:
          item = get(fact, 'obj') or get(fact, 'sub')
          label= get(fact, 'objLabel') or get(fact, 'subLabel')
          prop = get(fact, 'property')
          plbl = get(fact, 'propertyLabel')
          typ  = get(fact, 'type')
          tlbl = get(fact, 'typeLabel')
          # store values
          self.labels[item] = label
          self.labels[prop] = plbl
          self.labels[typ] = tlbl
          properties[prop] = properties.get(prop, []) + [(item, typ)]
          types[prop] = types.get(prop, []) + [typ]




        recommendations = {}
        recommendedprop = {}

        for prop, vals in sorted([(k,v) for k,v in properties.items()], key=lambda t:len(t[1])):
          print('\n=== {} ({}) ({}) ==='.format(self.wiki.extract_id(prop), self.labels.get(prop), len(vals)))
          # count how often a class occurs
          class_support = {}
          for item, typ in sorted(vals):
            print('val: {} ({})  --> {} ({})'.format(
              self.wiki.extract_id(item), self.labels.get(item),
              self.wiki.extract_id(typ), self.labels.get(typ)))
            class_support[typ] = class_support.get(typ,0) + 1
          if len(vals) > 2:
            print('support:')
            for k,v in sorted([(k,v) for k,v in class_support.items()], key=lambda t:t[1]):
              if v > 1:
                print('{} ({}): {}'.format(k, self.labels.get(k), v))
                if v == max(class_support.values()) and v/len(vals) > .6:
                  recommendations[k] = recommendations.get(k, []) + [(prop, v/len(vals))]
                  # if class has strong support, the associated property can be considered
                  # a potential recommendation
                  recommendedprop[prop] = v
            # get data from class inheritance traversal
            # but only if none of the classes found under this property has
            # a decisive support itself
            if max(class_support.values()) / len(vals) < -.2:
              print('support of common superclasses:')
              visits = self.common_superclass([t for i,t in vals])
              for k,v in sorted([(k,v) for k,v in visits.items()], key=lambda t:t[1]):
                if v > 1:
                  print('{} ({}): {}'.format(k, self.labels.get(k), v))
                  if v == max(visits.values()) and v/len(vals) > .7:
                    recommendations[k] = recommendations.get(k, []) + [(prop, v/len(vals))]
                    # only if there is a strong concept associated, current property can become
                    # recommendation
                    recommendedprop[prop] = v

              #   print('common superclasses:')
              #   superclasses = common_superclass([t for i,t in vals])
              #   for concept in superclasses:
              #     print('{} {}'.format(concept, labels.get(concept)))
        return {'types': recommendations, 'props': recommendedprop}



class SimpleRecommender(object):

    wiki = WikidataClient()


    def entity_rec(self, entity_id):

        query = template.format(entity=entity_id)

        res = self.wiki.sparql(query)

        properties = {}
        types = {}
        self.labels = {}

        for fact in res:
          item = get(fact, 'obj') or get(fact, 'sub')
          label = get(fact, 'objLabel') or get(fact, 'subLabel')
          prop = get(fact, 'property')
          plbl = get(fact, 'propertyLabel')
          typ = get(fact, 'type')
          tlbl = get(fact, 'typeLabel')
          # store values
          self.labels[item] = label
          self.labels[prop] = plbl
          self.labels[typ] = tlbl
          properties[prop] = properties.get(prop, []) + [(item, typ)]

        res = {"concepts": [], "properties": []}

        #recommendation_set = ConceptSet.objects.get(pk="recommendations")

        for prop, objects in properties.items():
          if len(LinkedProperty.objects.filter(linked_property=prop)) < 1:
            rcmd_property = LinkedProperty(
              id=prop.split('/')[-1],
              label=self.labels.get(prop).replace(' ','_')+"@Wikidata",
              comment=self.labels.get(prop),
              linked_property=prop
            )
            res["properties"].append(prop)
            rcmd_property.save()

          for obj in objects:
            item, typ = obj

            occurrence = PropertyConceptOccurrence(linked_property=prop, linked_concept=typ)
            occurrence.save()

            if len(LinkedConcept.objects.filter(linked_type=typ)) < 1:
              rcmd_concept = LinkedConcept(
                id=typ.split('/')[-1],
                endpoint="https://www.wikidata.org",
                retrieved_at=timezone.now(),
                label=self.labels.get(typ).replace(' ','_')+"@Wikidata",
                comment=self.labels.get(typ),
                linked_type=typ
              )
              res["concepts"].append(typ)
              rcmd_concept.save()

        return {"types": res}


    def linked_concepts(self):
        res = []
        linked_concepts = LinkedConcept.objects.all()
        for c in linked_concepts:
            count = len(PropertyConceptOccurrence.objects.filter(linked_concept=c.linked_type))
            if count > 1:
                linked_by_concepts = Concept.objects.filter(linked_concepts__linked_type__contains=c.linked_type.split('/')[-1])
                if len(linked_by_concepts) < 1:
                    res.append({"linked_concept": c.linked_type, "count": count, "label": c.label})
        res.sort(key=lambda e:e["count"], reverse=True)
        return {"linked_concepts": res[:len(res)/4]}


    def linked_properties(self):
        res = []
        linked_properties = LinkedProperty.objects.all()
        for p in linked_properties:
            occurences = PropertyConceptOccurrence.objects.filter(linked_property=p.linked_property)
            count = len(occurences)
            occurences = list(set([o.linked_concept for o in occurences.all()]))
            if count > 1:
                linked_by_properties = Property.objects.filter(linked_properties__linked_property__contains=p.linked_property.split('/'[-1]))
                if len(linked_by_properties) < 1:
                    res.append({"linked_property": p.linked_property, "count": count, "label": p.label, "types": occurences})
        res.sort(key=lambda e:e["count"], reverse=True)
        return {"linked_properties": res[:len(res)/4]}


    def recommend(self):
        concepts = {c["linked_concept"]:c for c in self.linked_concepts()["linked_concepts"]}

        properties = self.linked_properties()["linked_properties"]

        recommends = {"concepts":[], "properties":[]}

        for p in properties:
            for t in p["types"]:
                if t in concepts:
                    recommends["concepts"].append(t)
                    recommends["properties"].append(p["linked_property"])

        recommends =  {"concepts": list(set(recommends["concepts"])),
                "properties": list(set(recommends["properties"]))}

        for c in recommends["concepts"]:
            linked_concept = LinkedConcept.objects.get(linked_type=c)
            new_concept = Concept(id=linked_concept.id+"_"+linked_concept.label,
                                  label=linked_concept.comment,
                                  )
            new_concept.save()
            new_concept.linked_concepts.add(linked_concept)
            new_concept.save()

        return recommends