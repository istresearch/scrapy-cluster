'use strict';   // See note about 'use strict'; below

var myApp = angular.module('myApp', [
 'ngRoute',
]);

myApp.config(['$routeProvider',
     function($routeProvider) {
        $routeProvider.
        when('/', {
			templateUrl: '/static/partials/overview.html',
			controller: 'mainController'
		}).
		when('/kafka', {
			templateUrl: '/static/partials/kafka.html',
			controller: 'kafkaController'
		}).
		when('/crawlers', {
			templateUrl: '/static/partials/crawlers.html',
			controller: 'crawlersController'
		}).
		when('/redis', {
			templateUrl: '/static/partials/redis.html',
			controller: 'redisController'
		}).
		otherwise({
			redirectTo: '/'
		});
    }]);

myApp.controller('tabsController', ['$scope', function($scope) {
  $scope.tabs = [
      { link : '#/', label : 'Overview' },
      { link : '#/kafka', label : 'Kafka' },
      { link : '#/redis', label : 'Redis' },
      { link : '#/crawlers', label : 'Crawlers' }
    ];

  $scope.selectedTab = $scope.tabs[0];
  $scope.setSelectedTab = function(tab) {
    $scope.selectedTab = tab;
  }

  $scope.tabClass = function(tab) {
    if ($scope.selectedTab == tab) {
      return "active";
    } else {
      return "";
    }
  }
}]).controller('mainController', function($scope) {
    $scope.message = 'Overview!';
}).controller('kafkaController', function($scope) {
    $scope.message = 'Kafka...';
}).controller('redisController', function($scope) {
    $scope.message = 'Redis...';
}).controller('crawlersController', function($scope) {
    $scope.message = 'Crawler...';
});
