/**
 * AnnotatorMenu controller
 */
neonionApp.controller('AnnotatorMenuCtrl', ['$scope', '$window', '$location', '$cookies', '$interval',
    'cookieKeys', 'systemSettings', 'AnnotatorService', 'ConceptSetService', 'StatementService',
    function ($scope, $window, $location, $cookies, $interval, cookieKeys, systemSettings, AnnotatorService, ConceptSetService, StatementService) {
        "use strict";

        $scope.systemSettings = systemSettings;
        $scope.annotatorService = AnnotatorService;
        $scope.conceptSetService = ConceptSetService;

        $scope.mode = {
            commenting: {
                shortCut: "A",
                value: Annotator.Plugin.neonion.prototype.annotationModes.commenting
            },
            highlighting: {
                shortCut: "S",
                value: Annotator.Plugin.neonion.prototype.annotationModes.highlighting
            },
            conceptTagging: {
                shortCut: "D",
                value: Annotator.Plugin.neonion.prototype.annotationModes.conceptTagging
            }
        };

        $scope.shortCutModifier = {
            default: {
                modifierText: "Ctrl+Alt+"
            }
        };

        $scope.handleKeyDown = function (event) {
            if (event.ctrlKey && event.altKey) {
                for (var key in $scope.mode) {
                    if ($scope.mode[key].shortCut == String.fromCharCode(event.keyCode)) {
                        $scope.setAnnotationMode($scope.mode[key].value);
                        $scope.$apply();
                        break;
                    }
                }
            }
        };



        /**
         * Handle home click.
         */
        $scope.home = function() {
            if ($location.search().return) {
                window.location = $location.search().return;
            }
            else {
                window.location = "/";
            }
        };

        /**
         * Scrolls the view port to the last annotation.
         */
        $scope.scrollToLastAnnotation = function () {
            var annotation = AnnotatorService.getLastAnnotation();
            if (annotation) {
                AnnotatorService.scrollToAnnotation(annotation);
            }
        };

        $scope.getAnnotationMode = function () {
            if (Annotator && Annotator._instances.length >= 1) {
                return Annotator._instances[0].plugins.neonion.annotationMode();
            }
            else {
                return 1;
            }
        };

        $scope.setAnnotationMode = function (mode) {
            $cookies.put(cookieKeys.annotationMode, mode);
            Annotator._instances[0].plugins.neonion.annotationMode(mode);
        };

        $scope.toggleContributor = function (contributor) {
            var annotations = AnnotatorService.getUserAnnotations(contributor.user);
            if (!contributor.showAnnotation) {
                annotations.forEach(function (item) {
                    AnnotatorService.showAnnotation(item);
                });
                contributor.showAnnotation = true;

            } else {
                annotations.forEach(AnnotatorService.hideAnnotation);
                contributor.showAnnotation = false;
            }
        };

        $scope.startNamedEntityRecognition = function () {
            var span = angular.element('#nav-annotate>span');
            if (!span.hasClass('fa-spin')) {
                span.addClass('fa-spin');
                AnnotatorService.annotator().plugins.NER.recognize({
                    success: function (data) {
                        span.removeClass('fa-spin');
                    },
                    error: function () {
                        span.removeClass('fa-spin');
                    }
                });
            }
        };

        $scope.return = function () {
            $scope.$emit("returnEvent");
        };

        $scope.getConceptSet = function () {
            var conceptSetId = $scope.document ? $scope.document.concept_set : 'default';

            return ConceptSetService.resource.getDeep({id: conceptSetId},
                function (conceptSet) {
                    $scope.conceptSet = conceptSet;
                }).$promise;
        };

        $scope.switchConceptSet = function(conceptSetId) {
            console.log('change concept set to '+conceptSetId);
            $scope.document.concept_set = conceptSetId;

            ConceptSetService.resource.getDeep({id: conceptSetId},
                function (conceptSet) {
                    $scope.conceptSet = conceptSet;
                }).$promise.then(function(){
                    AnnotatorService.annotator().plugins.neonion.conceptSet($scope.conceptSet.concepts);
                    //$scope.document.$update($scope.return);
            });
        };

        $scope.recommendations = undefined;
        var recommender_job = $interval(function() {
                console.log("I AM FUCKING DOING MY FRICKNIG SCHEDULED JOB");
                StatementService.recommendations.get({},
                    function(results){
                        $scope.recommendations_incoming = results.concepts.length;
                    }).$promise.then($scope.loadRecommendations);
            },
            30000);

        $scope.loadRecommendations = function() {
            return ConceptSetService.resource.getDeep({id: "recommendations"},
                function(conceptSet){
                    $scope.recommendations = conceptSet;
                }
            ).$promise;
        };

        $scope.loadRecommendations();
        $scope.getConceptSet();

        $scope.reviewRecommendation = function(concept, keep) {
            console.log("concept "+concept.label);
                var recCS = ConceptSetService.resource.get({id:"recommendations"}, function() {
                    var ix = recCS.concepts.indexOf(concept.id);
                    recCS.concepts.splice(ix, 1);
                    recCS.$update().then($scope.loadRecommendations);
                });
                var declinedRecommendationsConceptSet = ConceptSetService.resource.get({id:"declined_recommendations"},
                    function() {
                        declinedRecommendationsConceptSet.concepts.push(concept.id);
                        declinedRecommendationsConceptSet.$update();
                    });
            if (keep) {
                var cs = ConceptSetService.resource.get({id:$scope.document.concept_set}, function() {
                    cs.concepts.push(concept.id);
                    cs.$update().then(
                        function(){$scope.switchConceptSet($scope.document.concept_set)}
                    );
                });

            }
        };



        /**
         * Find the right method, call on correct element.
         */
        $scope.enableFullscreen = function () {
            var element = angular.element('annotate-space')
            if (element.requestFullscreen) {
                element.requestFullscreen();

            } else if (element.mozRequestFullScreen) {
                element.mozRequestFullScreen();

            } else if (element.webkitRequestFullscreen) {
                element.webkitRequestFullscreen();

            } else if (element.msRequestFullscreen) {
                element.msRequestFullscreen();
            }
        };

        /**
         * Do semantic recommendations stuff.
         */
        $scope.checkForSuggestions = function() {
            console.log("alright");

        };

        $scope.getEntities = function() {
            var items = $.map(AnnotatorService.getAnnotationObjects(), function(elem){
                return elem.oa.hasBody.identifiedAs;
            });
            return items;
        }

    }]);