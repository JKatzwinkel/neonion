neonionApp.factory('LinkedPropertyService', ['$resource',
        function ($resource) {
            return $resource('/api/linkedproperties/:id',
                {id: '@id'},
                {
                    'save': {method: 'POST', url: '/api/linkedproperties/'},
                    'update': {method: 'PUT'},
                }
            );
        }]
);
