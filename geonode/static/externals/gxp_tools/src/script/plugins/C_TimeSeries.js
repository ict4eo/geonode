/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */
 
/**
 * Author ICT4EO - Bolelang
 */

/**
 * @requires plugins/Tool.js
 * @requires GeoExt/widgets/Popup.js
 * @requires OpenLayers/Control/WMSGetFeatureInfo.js
 * @requires OpenLayers/Format/WMSGetFeatureInfo.js
 */
 
/** api: (define)
 *  module = gxp.plugins
 *  class = TimeSeriesPopup
 */
 
/** api: (extends)
 *  plugins/Tool.js
 */
 
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: TimeSeriesPopup(config)
 *
 *    Create a new popup which displays time series data for a particular point of interest
 */
 
gxp.plugins.TimeSeriesPopup = Ext.extend(gxp.plugins.Tool, {
    /** api: ptype = gxp_timeseriespopup */
    ptype: "gxp_timeseriespopup",
    
    /** api: config[outputTarget]
     *  ``String`` Popups created by this tool are added to the map by default.
     */
    outputTarget: "map",
    
    /** private: property[popupCache]
     *  ``Object``
     */
    popupCache: null,
    
    /** api: config[infoActionTip]
     *  ``String``
     *  Text for feature info action tooltip (i18n).
     */
    infoActionTip: "Get Time Series info",
    
    /** api: config[popupTitle]
     *  ``String``
     *  Title for info popup (i18n).
     */
    popupTitle: "Time Series Info",
    
    /** api: config[text]
     *  ``String`` Text for the TimeSeriesInfo button (i18n).
     */
    buttonText: "Time Series",
    
    /** api: config[format]
     *  ``String`` Either "html" or "grid". If set to "grid", GML will be
     *  requested from the server and displayed in an Ext.PropertyGrid.
     *  Otherwise, the html output from the server will be displayed as-is.
     *  Default is "html".
     */
    format: "html",
    
        /** api: method[addActions]
     */
    addActions: function() {
        this.popupCache = {};
        var map= this.target.mapPanel.map;
        var actions = gxp.plugins.TimeSeriesPopup.superclass.addActions.call(this, [{
            tooltip: this.infoActionTip,
            iconCls: "gxp-icon-selectfeature", // find appropriate icon-where?
            buttonText: this.buttonText,
            toggleGroup: this.toggleGroup,
            enableToggle: true,
            allowDepress: true,
            map: map,
            toggleHandler: function(button, pressed) {
                for (var i = 0, len = info.controls.length; i < len; i++){
                    if (pressed) {
                        info.controls[i].activate();
                    } else {
                        info.controls[i].deactivate();
                    }
                }
             }
        }]);
        
        var infoButton = this.actions[0].items[0];

        var info = {controls: []};
        
        //function that does something and displays in a pop up:
        var updateInfo = function() {
            var queryableLayers = this.target.mapPanel.layers.queryBy(function(x){
                return x.get("queryable");
            });

            var map = this.target.mapPanel.map;
            var control;
            for (var i = 0, len = info.controls.length; i < len; i++){
                control = info.controls[i];
                control.deactivate();  // TODO: remove when http://trac.openlayers.org/ticket/2130 is closed
                control.destroy();
            }

            info.controls = [];
            queryableLayers.each(function(x){
                var layer = x.getLayer();
                var infoFormat = x.get("infoFormat");
                //infoFormat = "text/plain"; 
                infoFormat = "application/vnd.ogc.gml"
                if (infoFormat === undefined) {
                    // TODO: check if chosen format exists in infoFormats array
                    // TODO: this will not work for WMS 1.3 (text/xml instead for GML)
                    infoFormat = this.format == "html" ? "text/html" : "application/vnd.ogc.gml";                    
                }
                var control = new OpenLayers.Control.WMSGetFeatureInfo(Ext.applyIf({
                    url: layer.url,
                    queryVisible: true,
                    layers: [layer],
                    infoFormat: infoFormat,
                    eventListeners: {
                        getfeatureinfo: function(evt) {                            
                            //alert(evt.features[0].attributes.id)                            
                            var title = x.get("title") || x.get("name");
                            this.displayPopup(evt, title, evt.features[0].attributes.id);
                        },
                        scope: this
                    }
                }, this.controlOptions));
                map.addControl(control);
                info.controls.push(control);
                if(infoButton.pressed) {
                    control.activate();
                }
            }, this);

        };
        
        this.target.mapPanel.layers.on("update", updateInfo, this);
                
        return actions;
    },
    
     /** private: method[displayPopup]
     * :arg evt: the event object from a 
     *     :class:`OpenLayers.Control.GetFeatureInfo` control
     * :arg title: a String to use for the title of the results section 
     *     reporting the info to the user
     * :arg text: ``String`` Body text.
     */
    displayPopup: function(evt, title, featureid){
      var popup;
      var popupKey = evt.xy.x + "." + evt.xy.y;
      //featureinfo = featureinfo || {};
      //alert(featureid)
      if (!(popupKey in this.popupCache)) {
        this.removeOutput();
        popup = this.addOutput({
            xtype: "gx_popup",
            id: "test",
            title: this.popupTitle + " : " + featureid,
            layout: "fit",
            fill: false,
            autoScroll: true,
            autoLoad: {url: '/static/externals/D3/d3_graphs.html', scripts: true }, //html file containing d3 code, params:{param1:"a", param2:"b"}
            location: evt.feature,
            map: this.target.mapPanel,
            width: 550,
            height: 350,
            items: [{
                xtype: "hidden",
                id: "fid",
                value: featureid,
            }],
            defaults: {
                layout: "fit",
                autoScroll: true,
                autoHeight: true,
                autoWidth: true,
                collapsible: true,
            }
        });
        //popup.on();
        popup.on({                    
                close: (function(key) {
                    return function(panel){
                        delete this.popupCache[key];
                    };
                })(popupKey),
                scope: this
        });
        this.popupCache[popupKey] = popup;
      } else {
            popup = this.popupCache[popupKey];
        }
    }

});

Ext.preg(gxp.plugins.TimeSeriesPopup.prototype.ptype, gxp.plugins.TimeSeriesPopup);
