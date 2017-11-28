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
                {sId: '@sId', pId: '@pId'}
            ),
            references: $resource('/api/wikidata/reference/:sId/:pId/:oId/:documentUrl',
                {sId: '@sId', pId: '@pId', oId: '@oId', documentUrl: '@documentUrl'},
                {
                    get: {method: 'GET'},
                    save: {method: 'POST'}
                }
            ),
            recommended_types: $resource('/api/wikidata/recommend/entity/:cId/:sId',
                {cId: '@cId', sId: '@sId'}
            ),
            recommendations: $resource('/api/wikidata/recommend')
        };
    }]
);
