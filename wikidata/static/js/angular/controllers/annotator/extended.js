neonionApp.controller('AnnotatorCtrlExtended', ['$scope', '$controller', '$resource', '$interval', function($scope, $controller, $resource, $interval) {

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
	$scope.Recommendations = $resource('/wikidata/recommendedconcepts', {});

	// actual vocabulary recommendations
	$scope.recommendedTerms = {};


	$scope.updateRecommender = function(event) {
		console.log(event)
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

	var recommendationLabelResolverJob = $interval(function() {
		console.log('running scheduled label resolving job');
		for (var i=0; i<$scope.recommendedTerms.length; i++) {
			var term = $scope.recommendedTerms[i];
			//
		}
	}, 6000);



}]);
