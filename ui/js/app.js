angular.module('uiApp', ['ngRoute', 'ngResource','uiApp.controllers','uiApp.services']);

angular.module('uiApp').config(function($routeProvider) {
	$routeProvider
		.when('/', {
			templateUrl: 'pages/overview.html',
			controller: 'mainController'
		})
		.when('/kafka', {
			templateUrl: 'pages/kafka.html',
			controller: 'kafkaController'
		})
		.when('/crawlers', {
			templateUrl: 'pages/crawlers.html',
			controller: 'crawlersController'
		})
		.when('/redis', {
			templateUrl: 'pages/redis.html',
			controller: 'redisController'
		})
		.when('/debug', {
			templateUrl: 'pages/debug.html',
			controller: 'debugController'
		})
		.otherwise({
			redirectTo: '/'
		});
});