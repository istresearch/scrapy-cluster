angular.module('uiApp.controllers',[]).controller('tabsController', function($scope) {
  $scope.tabs = [
      { link : '#/', label : 'Overview' },
      { link : '#/kafka', label : 'Kafka' },
      { link : '#/redis', label : 'Redis' },
      { link : '#/crawlers', label : 'Crawlers' },
      { link : '#/debug', label : 'Debug' }

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
}).controller('mainController', function($scope) {
    $scope.message = 'Overview!';
}).controller('kafkaController', function($scope) {
    $scope.message = 'Kafka...';
}).controller('redisController', function($scope) {
    $scope.message = 'Redis...';
}).controller('crawlersController', function($scope) {
    $scope.message = 'Crawler...';
}).controller('debugController', function($scope) {
    $scope.message = 'Debug...';
});