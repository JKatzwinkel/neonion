/**
 * Created by thor on 9/16/17.
 */
neonionApp.factory('StatementService', ['$resource',
    function ($resource) {
        return $resource('/store/:groupId/:docId/groupedstatements',
            {docId: '@docId', groupId: '@groupId'},
            {
                'getStatements': {
                    method: 'GET',
                    params: {},
                    cache: true,
                    transformResponse: function(data, header) {
                        var jsonData = angular.fromJson(data);
                        return jsonData;
                    }
                }
            }
        );
    }]
);
