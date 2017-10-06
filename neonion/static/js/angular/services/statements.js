/**
 * Created by thor on 9/16/17.
 */
neonionApp.factory('StatementService', ['$resource',
    function ($resource) {
        return {
            statements: $resource('/store/:groupId/:docId/groupedstatements',
                {docId: '@docId', groupId: '@groupId'}
            ),
            proofs: $resource('/api/wikidata/statement/:sId/:pId/',
                {sId: '@sId', pId: '@pId'})
        };
    }]
);
