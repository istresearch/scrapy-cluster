'use strict';

var uiApp = angular.module('uiApp', [
 'ngRoute',
]);

uiApp.config(['$routeProvider',
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

uiApp.controller('tabsController', ['$scope', function($scope) {
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
}]).controller('mainController', function($scope, $http, API_ENDPOINT) {
     $scope.loadstatus=function(){
         $http.get(API_ENDPOINT.url)
         .success(function(response){
              $scope.data=response;
         })
         .error(function(){
              alert("An unexpected error occurred!");
         });
     }

    // create a blank object to handle form data.
    $scope.request = {};

    // calling our submit function.
    $scope.submitForm = function() {
    var reqObj = {
            url : $scope.request.url,
            appid : "uiservice",
            crawlid : $scope.request.crawlid,
            maxdepth : $scope.request.maxdepth,
            priority : $scope.request.priority,
    };

    // Posting data to php file
    $http({
      method  : 'POST',
      url     : API_ENDPOINT.url + '/feed',
      data    : angular.toJson(reqObj), //forms user object
      headers : {'Content-Type': 'application/json'}
     })
     .success(function(data) {
        if (data.errors) {
          $scope.error = data.errors;
        } else {
          $scope.message = data.message;
        }
      });
    };

}).controller('kafkaController', function($scope) {
    $scope.message = 'Kafka...';
}).controller('redisController', function($scope) {
    $scope.message = 'Redis...';
}).controller('crawlersController', function($scope) {
    $scope.message = 'Crawler...';
});
