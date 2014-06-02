;(function () {
  var $refresher = null;

  var AboutCtrl = function (hash) {
    getHtml('about').then(function (html) {
      $('#controller-view-outer').html(html);
    });
  }

  var BuildingNewCtrl = function (hash) {
    getHtml('building_new').then(function (html) {
      $('#controller-view-outer').html(html);
      $('input[name="name"]')    .val(chance.street());
      $('input[name="n_floors"]').val(chance.integer({min: 8, max: 12}));
      $('input[name="n_cars"]')  .val(chance.integer({min: 1, max: 8}));
      $('input[name="speed"]')   .val(chance.floating({min: 1, max: 4, fixed: 1}));
      $('form').submit(function (event) {
        event.preventDefault();
        var formData = {};
        _.each($('form').serializeArray(), function (kv) {
          formData[kv.name] = kv.value;
        });
        formData['name'] = _.string.dasherize(formData['name']).slice(1);
        Q(jQuery.ajax({
          type: 'POST',
          url: '/api/v1/buildings',
          contentType: 'application/json; charset=utf-8',
          data: JSON.stringify(formData)})
        ).then(renderNavbar).then(function () {
          route('buildings/' + formData['name']);
        });
      });
    });
  };

  var BuildingShowCtrl = function (hash) {
    var name = hash.slice(hash.indexOf('/') + 1);
    
    getHtml('building_show').then(function (template) {
      var _updateClass = function (pair) {
        var fst = $(pair[0])
          , cls = $(pair[1]).attr('class');
        if (fst.attr('class') != cls)
          fst.attr('class', cls);
      }

      var refreshBuilding = function () {
        getBuildingStatus(name)
        .catch(function () {
          if ($refresher) {
            clearInterval($refresher);
            $refresher = null;
          }
        })
        .then(function (resp) {
          var status = resp.status
            , locals = status
            , title  = _.escape(_.string.titleize(_.string.humanize(status.name)));
          _.extend(locals, {
            title: title
          })
          html = $(_.template(template, locals));
          _.each(_.zip($('.row-floor-label'), html.find('.row-floor-label')), _updateClass);
          _.each(_.zip($('.button.car'), html.find('.button.car')), _updateClass);
        });
      };
      var renderBuilding = function () {
        getBuildingStatus(name).then(function (resp) {
          var status = resp.status
            , locals = status
            , title  = _.escape(_.string.titleize(_.string.humanize(status.name)));
          _.extend(locals, {
            title: title
          })
          html = _.template(template, locals);
          $('#controller-view-outer').html(html);
          $(document).foundation({
            dropdown: {active_class: 'open'}
          });
          $('.button[data-floor-action="call"]').click(function () {
            var $el = $(this);
            Q(jQuery.ajax({
              type: 'POST',
              url: '/api/v1/buildings/' + name + '/floors/' + $el.attr('data-floor-i') + '/buttons/call'
            })).then(refreshBuilding)
          });
          $('.button[data-car-action="send"]').click(function () {
            var $el = $(this),
                car_i = $el.attr('data-car-i');
            $('button[data-dropdown="car-buttons-' + car_i + '"]:not(.hide)').click();
            Q(jQuery.ajax({
              type: 'POST',
              url: '/api/v1/buildings/' + name + '/cars/' + car_i + '/buttons/' + $el.attr('data-car-floor')
            })).then(refreshBuilding)
          });
          $('.button[data-car-action="toggle"]').click(function () {
            var $el = $(this),
                car_i = $el.attr('data-car-i');
            $('button[data-dropdown="car-buttons-' + car_i + '"]:not(.hide)').click();
            Q(jQuery.ajax({
              type: 'POST',
              url: '/api/v1/buildings/' + name + '/cars/' + car_i + '/buttons/toggle'
            })).then(refreshBuilding)
          });
        });
      };

      renderBuilding();
      $refresher = setInterval(_.bind(refreshBuilding, this), 1000);
    });
  };

  var controllers = {
    'new':       BuildingNewCtrl,
    'buildings': BuildingShowCtrl,
    'about':     AboutCtrl
  };

  var getStatus = function () {
    return Q(jQuery.ajax({
      type: 'GET',
      url: '/api/v1/status',
      dataType: 'json'
    }));
  };

  var getBuildingStatus = function (name) {
    return Q(jQuery.ajax({
      type: 'GET',
      url: '/api/v1/buildings/' + name + '/status',
      dataType: 'json'
    }));
  };

  var getHtml = function (template_name) {
    return Q($.ajax({
      type: 'GET',
      url: '/html/_' + template_name + '.html'
    }));
  };

  var loadTabs = function (status) {
    $('.buildings-list-nav').empty();
    _.each(_.keys(status.buildings), function (name) {
      var href  = '#buildings/' + _.escape(name)
        , title = _.escape(_.string.titleize(_.string.humanize(name)));
      // TODO: Тут я не совладал с вёрсткой, но получилось симпатично.
      $('.buildings-list-nav').append(
        '<li data-tab-building="' + name + '">'
        // + '<div class="row collapse">'
          // + '<div class="small-1 columns">'
            + '<a href="' + href + '"><nobr>' + title + '</nobr></a> '
          // + '</div>'
          // + '<div class="small-1 columns">'
            + '<button class="button alert" data-tab-action="destroy"><i class="fi-x"></i>'
            + '</button>'
          // + '</div>'
        // + '</div>'
        + '</li>'
      );
    });
    $('[data-tab-action="destroy"]').click(function () {
      var $tab   = $(this).parent('li')
        , name   = $tab.attr('data-tab-building')
        , active = $tab.hasClass('active');
      Q(jQuery.ajax({
        type: 'DELETE',
        url: '/api/v1/buildings/' + name,
        contentType: 'application/json; charset=utf-8'})
      ).then(loadTabs)
       .then(renderNavbar)
       .then(function () {
        if (active) {
          route('new');
        }
      });
    });
  };

  var renderNavbar = function () {
    return getStatus().then(function (resp) {
      loadTabs(resp.status);
    });
  };

  var route = function () {
    if ($refresher) {
      clearInterval($refresher);
      $refresher = null;
    }

    if (arguments.length > 0 && typeof(arguments[0]) == 'string') {
      window.location.hash = arguments[0];  // вызовет событие hashchange
      return;
    }

    var hash = window.location.hash || '#new';
    if (hash.length > 1) {
      $('li a[href!="' + hash +'"]').parents('li').toggleClass('active', false);
      $('li a[href="' + hash +'"]').parents('li').toggleClass('active', true);

      var ctrlName = hash.replace(/^#(\w+)\/?.*/, '$1')
        , ctrl = controllers[ctrlName];
      if (typeof(ctrl) == 'function') {
        ctrl(hash);
      }
    }
  };

  jQuery(function () {
    renderNavbar().then(route);
  });
  jQuery(window).on('hashchange', route);
})();