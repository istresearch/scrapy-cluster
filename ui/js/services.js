angular.module('uiApp.services',[]).factory('jsonStats',function($resource){
    return $resource('http://localhost:5000/getStats',{},{
        update: {
            method: 'GET'
        }
    });
}).service('popupService',function($window){
    this.showPopup=function(message){
        return $window.confirm(message);
    }
});