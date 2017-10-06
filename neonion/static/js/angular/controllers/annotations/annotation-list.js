neonionApp.controller('AnnotationListCtrl', ['$scope', '$http', '$filter', 'CommonService', 'DocumentService',
    'GroupService', 'AnnotationStoreService', 'StatementService',
    function ($scope, $http, $filter, CommonService, DocumentService, GroupService, AnnotationStoreService, StatementService) {
        "use strict";

        $scope.pageNum = 0;
        $scope.stepSize = 50;
        $scope.annotations = [];
        $scope.statements = [];

        $scope.exportFields = {
            baseFields : function() {
                return  [
                    'oa.@id', 'oa.annotatedBy.mbox.@id', 'oa.motivatedBy', 'oa.annotatedAt', 
                    'oa.hasTarget.hasSource.@id', 'oa.hasTarget.hasSelector.conformsTo', 'oa.hasTarget.hasSelector.value',
                    'oa.hasBody.@type'
                ];   
            },
            commentFields: function() {
                return $scope.exportFields.baseFields().concat(['oa.hasBody.chars']);
            },
            highlightFields: function() {
                return $scope.exportFields.baseFields();  
            },
            graph: function() {
                return $scope.exportFields.baseFields().concat([
                    'oa.hasBody.contextualizedAs', 'oa.hasBody.classifiedAs', 'oa.hasBody.identifiedAs', 'oa.hasBody.label',
                    'oa.hasBody.relation', 'oa.hasTarget.hasSelector.source', 'oa.hasTarget.hasSelector.target'
                ]);
            },
        };

        $scope.getQueryParams = function (pageNum) {
            return {
                'offset': pageNum * $scope.stepSize,
                'limit': $scope.stepSize
            };
        };

        $scope.queryGroupNames = function () {
            return GroupService.queryGroupNames(function (data) {
                $scope.groupNames = data;
            }).$promise;
        };

        $scope.queryDocumentTitles = function () {
            return DocumentService.queryTitles(function (data) {
                $scope.documentTitles = data;
            }).$promise;
        };

        $scope.queryCurrentUser = function () {
            return CommonService.getCurrentUser(function (data) {
                $scope.user = data;
            }).$promise;
        };

        $scope.queryStatements = function () {
            $scope.statements = $scope.linkedAnnotations();
        };

        $scope.getDocumentStatements = function () {
            var documentId = $scope.document.id;
            var groupId = $scope.groupId;
            console.log('I want statement list for doc '+documentId);

            return StatementService.statements.get({docId: documentId, groupId: groupId},
                function (statements) {
                    // copy to controller scope
                    $scope.statementsByEntity = statements;
                }
            ).$promise;
        };

        $scope.validateStatements = function() {
            for (var subj in $scope.statementsByEntity) {

                var statements = $scope.statementsByEntity[subj];

                if (statements.properties) {

                    for (var prop in statements.properties) {

                        StatementService.proofs.get({sId: subj, pId: prop},
                            function(result) {

                                var subj = result.subject;
                                var prop = result.property;

                                var values = $scope.statementsByEntity[subj].properties[prop];
                                for (var value in values) {
                                    var status = values[value];
                                    if (result.objects.includes(value)) {
                                        status.exists = 1;
                                    } else {
                                        status.exists = 0;
                                    }
                                }

                            }
                        );

                    }

                }

            }
        }


        $scope.queryAnnotations = function (pageNum) {
            pageNum = pageNum | 0;
            return AnnotationStoreService.search($scope.getQueryParams(pageNum), function (annotations) {
                if (annotations.length > 0) {
                    $scope.annotations = $scope.annotations.concat(annotations.filter(function (item) {
                        return $scope.documentTitles.hasOwnProperty(item.uri);
                    }));
                    $scope.queryAnnotations(pageNum + 1);
                }
            }).$promise;
        };

        $scope.downloadComments = function (format) {
            var annotations = $filter('filterByCommentAnnotation')($scope.annotations)
                .filter($scope.filterCommentAnnotations);
            $scope.download(annotations, $scope.exportFields.commentFields(), format, "comments_");
        };

        $scope.downloadHighlights = function (format) {
            var annotations = $filter('filterByHighlightAnnotation')($scope.annotations)
                .filter($scope.filterHighlightAnnotation);
            $scope.download(annotations, $scope.exportFields.highlightFields(), format, "highlights_");
        };

        $scope.linkedAnnotations = function () {
            // filter for concept annotations
            var annotations = $filter('filterByConceptAnnotation')($scope.annotations)
                .filter($scope.filterConceptAnnotations);
            console.log('number of concept annotations: '+annotations.length);
            // filter for linked annotations - only export linked annotations that are relevant
            var linkedAnnotations = $filter('filterByLinkedAnnotation')($scope.annotations);
            console.log('number of linked  annotations: '+linkedAnnotations.length);

            /*var statements = linkedAnnotations.map(function(annotation){
                return {
                    "subject": {},
                    "predicate": annotation,
                    "object": {}
                };
            });*/
                /*// check if the subject is present in the array of annotations
                .filter(function (linkage) {
                    return annotations.some(function (annotation) {
                        return annotation['oa']['@id'] == linkage['oa']['hasTarget']['hasSelector']['source'];
                    })
                })
                // check if the objects is present in the array of annotations
                .filter(function (linkage) {
                    return annotations.some(function (annotation) {
                        return annotation['oa']['@id'] == linkage['oa']['hasTarget']['hasSelector']['target'];
                    });
                });*/
            console.log('number of linked annotations: '+linkedAnnotations.length);
            return linkedAnnotations;
        };

        //$scope.linkedAnnotation()

        $scope.downloadConceptsAndStatements = function (format) {
            // filter for concept annotations
            var annotations = $filter('filterByConceptAnnotation')($scope.annotations)
                .filter($scope.filterConceptAnnotations);
            // filter for linked annotations
            var linkedAnnotations = $scope.linkedAnnotations();

            $scope.download(annotations.concat(linkedAnnotations),
                $scope.exportFields.graph(), format, "knowledge_");

        };

        $scope.download = function (data, properties, format, filePrefix) {
            filePrefix = filePrefix || 'annotations_';
            if (format.toLowerCase() === 'csv') {
                var data = $scope.exportCSV(data, properties);
                var fileName = filePrefix + new Date().getTime() + '.csv';
                var link = document.createElement('a');
                link.setAttribute('href', data);
                link.setAttribute('target', '_blank');
                link.setAttribute('download', fileName);
                link.click();
            }
        };

        $scope.filterCommonFields = function (annotation) {
            if (CommonService.filter.query.length > 0) {
                var show = false;
                // filter by user
                if (annotation.hasOwnProperty("neonion")) {
                    show |= annotation['neonion']['creator'].toLowerCase().indexOf(CommonService.filter.query.toLowerCase()) != -1;
                }
                // filter by document name
                if ($scope.documentTitles.hasOwnProperty(annotation.uri)) {
                    show |= $scope.documentTitles[annotation.uri].toLowerCase().indexOf(CommonService.filter.query.toLowerCase()) != -1;
                }
                // filter by seletected text
                show |= annotation.quote.toLowerCase().indexOf(CommonService.filter.query.toLowerCase()) != -1;
                return show;
            }
            return true;
        }

        $scope.filterCommentAnnotations = function (annotation) {
            if (CommonService.filter.query.length > 0) {
                var show = $scope.filterCommonFields(annotation);
                show |= annotation.text.toLowerCase().indexOf(CommonService.filter.query.toLowerCase()) != -1;
                return show;
            }
            return true;
        };

        $scope.filterConceptAnnotations = function (annotation) {
            if (CommonService.filter.query.length > 0) {
                var show = $scope.filterCommonFields(annotation);
                if (annotation.hasOwnProperty("rdf")) {
                    show |= annotation['oa']['hasBody']['label'].toLowerCase().indexOf(CommonService.filter.query.toLowerCase()) != -1;                 
                }
                return show;
            }
            return true;
        };

        $scope.filterHighlightAnnotation = function (annotation) {
            return $scope.filterCommonFields(annotation);
        };

        // execute promise chain
        $scope.queryGroupNames()
            .then($scope.queryDocumentTitles)
            .then($scope.queryCurrentUser)
            .then($scope.queryAnnotations)
            .then($scope.getDocumentStatements)
            .then($scope.validateStatements);


        /*$scope.whatever = "FFFF...";
        // try and call some place
        var promise = $http.get('/api/wikidata/statement/Q86059/P31');

        promise.then(
            function(payload) {
                $scope.whatever = payload.status;
                $scope.statementsByEntity['Q86059'].properties['P31']["Q5"].exists = 1;
            },
            function(errorPayload) {
                console.log('FUCK STH WENT WRONGGG!');
                console.log(errorPayload.data);
                console.log(errorPayload.status);
                console.log(errorPayload.headers);
            });*/


    }
]);