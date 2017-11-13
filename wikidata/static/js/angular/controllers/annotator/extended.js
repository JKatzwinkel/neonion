neonionApp.controller('AnnotatorCtrlExtended', ['$scope', '$controller', '$resource', '$interval', '$timeout', 'LinkedConceptService',
	function($scope, $controller, $resource, $interval, $timeout, LinkedConceptService) {

	angular.extend(this, $controller('AnnotatorCtrl', {$scope: $scope}));
	$scope.annotator = undefined;

	console.log('hehehe');

	$scope.ConceptRecommender = $resource('/wikidata/related/types/doc/:docId/concept/:conceptId',
		{docId:'@docId',conceptId:'@conceptId'},
		{
			'run': {method: 'PUT'}
		}
	);
	$scope.Recommendations = $resource('/wikidata/recommendedconcepts/:id', {id:'@id'},
		{
			'get': {method: 'GET'},
			'update': {method: 'PUT'},
		}
	);
	$scope.WikidataItemLabelResolver = $resource('/wikidata/entities/label/:id', {id:'@id'},
		{
			'update': {method: 'PUT'},
		}
	);


	// actual vocabulary recommendations
	$scope.recommended = {};

	$scope.recommendationCount = function() {
		return Object.keys($scope.recommended).length;
	}


	$scope.updateRecommender = function(event) {
		var annotation = event.annotation || event;

		if (annotation) {
			var cid = annotation.oa.hasBody.classifiedAs.split("/").pop();
		} else {
			var cid = undefined;
		}

		$scope.ConceptRecommender.run({docId:$scope.documentId, conceptId:cid},
			function(result) {
				console.log(result);
				for (var i=0; i<result.length; i++) {
					rec = result[i];
					console.log(i, rec);
				}
			}).$promise.then($scope.bla);


	}

	$scope.bla = function() {
		console.log('Hm');
	}

	$scope.openRecommendations = function() {
	};

  $scope.$on('allPagesRendered', function (event) {
		console.log('annotator fragezeichen');
		console.log( $scope.annotator);
  });

	var initialHookJob = $interval(function() {
		console.log('hook up wikidata/recommender extensions with annotator.js');
		if (!$scope.annotator) {
			console.log('OK better subscribe to this annotator');
	    $scope.annotator = angular.element("#document-body").data("annotator");
	    $scope.annotator.subscribe("annotationEditorSubmit", $scope.updateRecommender)
											.subscribe("annotationDeleted", $scope.updateRecommender);
			$interval.cancel(initialHookJob);
		}
	}, 5000);


	// reifies the recommended vocabulary term itself (linked_property e.g.) and extracts 
	// the linked resource (linked_type e.g.) so that it can be accessed in html template
	$scope.resolveLinkedResource = function(term) {
		LinkedConceptService.get({id: term.linked_concept},
			function(linked_concept){
				//$scope.recommended[term.id].
				term.linked_resource = linked_concept.linked_type;
			}
		);
	}

	// gets label and description for a linkedconcept linked to a recommendation and updates recommendation accordingly
	$scope.resolveLabels = function(term) {
		LinkedConceptService.get({id: term.linked_concept},
			function(linked_concept){

				// if linked_concept linked to recommendation has no label itself, we need to query wiki module
				if (linked_concept.label.length < 1) {
					$scope.WikidataItemLabelResolver.get({id: linked_concept.linked_type},
						function(label_desc) {
							linked_concept.label = label_desc.label;
							linked_concept.comment = label_desc.description;
							linked_concept.$update();

						});
				}

				// then we need to retrieve a fresh instance of the recommendation object (in order to be able to $update)
				// and we can update its label and description just like we did with its linked concept
				$scope.Recommendations.get({id: term.id},
					function(recommendation) {
						console.log(recommendation);
						recommendation.label = linked_concept.label;
						recommendation.comment = linked_concept.comment;
						recommendation.$update();
					});

			}
		);

	};


	// schedule job that frequently resolves labels of current recommendations, if necessary
	var recommendationLabelResolverJob = $interval(function() {
			Object.keys($scope.recommended).forEach(function(id){
				var term = $scope.recommended[id];
				if (term.label.length < 1) {
					$scope.resolveLabels(term);
				} 
				else if (!term.linked_resource) {
					$scope.resolveLinkedResource(term);

				}
			}
		);
	}, 6000);

  var checkforRecommendationsJob = $interval(function() {
		$scope.Recommendations.query({},
			function(results) {
				console.log('yeah');
				results.forEach(function(result){
					if (!$scope.recommended.hasOwnProperty(result.id)) {
						$scope.recommended[result.id] = result;
					}
				});
			})
	}, 10000);

	$scope.$on('$destroy', function() {
		console.log('kill job');
		$interval.cancel(recommendationLabelResolverJob);
		$interval.cancel(checkforRecommendationsJob);
	});

}]);
