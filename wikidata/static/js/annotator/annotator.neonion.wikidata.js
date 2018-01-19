(function () {
	"use strict";


	console.log('what is going on here')

	Annotator.Plugin.neonion.prototype.widgets['lelWhatNow'] = function (scope, options) {
		var factory = {
			counter: 0
		};

		factory.load = function () {

			console.log('LOADING!');
			console.log(scope.options);

			scope.options.lookup = {
			  prefix: '/wikidata',
				urls: {
					search: "/itemsearch"
				}
			};

			scope.annotator.subscribe('annotationEditorShown', function (editor, annotation) {

				console.log(annotation);
				console.log('LOOOOOOLL!!!!!!');
				console.log(scope.options);

			});

			scope.annotator.subscribe('annotationEditorHidden', function () {
				factory.counter ++;
				console.log('DOOOOONE!');
				console.log(factory.counter);
			});

		};

		return factory;

	}
})();
