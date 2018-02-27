neonionApp.controller('AnnotatorCtrlExtended', ['$scope', '$controller', '$resource', '$interval', '$timeout', 'LinkedConceptService',
	function($scope, $controller, $resource, $interval, $timeout, LinkedConceptService) {

	angular.extend(this, $controller('AnnotatorCtrl', {$scope: $scope}));
	$scope.annotator = undefined;

	console.log('hehehe');
	//$scope.annotator.subscribe("annotationEditorSubmit", $scope.perform);
	//console.log($scope.annotator);
	//

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
	$scope.recommendedTerms = {};


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
			/*$scope.Recommendations.query({},
				function(result) {
					$scope.recommendedTerms = result;
				});*/
			$interval.cancel(initialHookJob);
		}
	}, 5000);



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


	var recommendationLabelResolverJob = $timeout(function() {
		console.log('running scheduled label resolving job');

		for (var i=0; i<$scope.recommendedTerms.length; i++) {

			var term = $scope.recommendedTerms[i];

			if (term.label.length < 1) {
				$scope.resolveLabels(term);
			}

		}
	}, 6000);

	$scope.Recommendations.query({},
		function(result) {
			console.log('yeah');
			$scope.recommendedTerms = result;
		}).$promise.then($scope.bla);

	$scope.$on('$destroy', function() {
		console.log('kill job');
		$interval.cancel(recommendationLabelResolverJob);
	});

}]);
