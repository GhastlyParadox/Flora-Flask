/*
This is similar to index.js/index.html but without the search and results table sections.
It also takes any of the following url query parameters and filters the results display accordingly:
common_name
family
genus
scientific_name (for species search)
county
Example url: http://localhost:63343/mi-flora-webmap/index_map_only.html?genus=acer

The formatting (symbology) of the mapped points will need some work to be what they're looking for.
 */
let layer;
let layerAll;
let countyLayer;
let countyOutlineLayer;
let layerLookupItemUrl = "https://services1.arcgis.com/4ezfu5dIwH83BUNL/arcgis/rest/services/Michigan_Flora_Current_Layer_ID_(Public_View)/FeatureServer";
let layerPointsUrl ="https://services1.arcgis.com/4ezfu5dIwH83BUNL/ArcGIS/rest/services/Michigan_Flora_Specimens/FeatureServer/0";  //"https://services1.arcgis.com/4ezfu5dIwH83BUNL/arcgis/rest/services/MiFlora_2019_0403/FeatureServer/0" //https://services1.arcgis.com/4ezfu5dIwH83BUNL/arcgis/rest/services/MiFlora_2019_0320_Locations/FeatureServer/0";
let layerAllUrl = "https://services1.arcgis.com/4ezfu5dIwH83BUNL/ArcGIS/rest/services/Michigan_Flora_Specimens/FeatureServer/0"; //"https://services1.arcgis.com/4ezfu5dIwH83BUNL/arcgis/rest/services/MiFlora_2019_0403/FeatureServer/0" //https://services1.arcgis.com/4ezfu5dIwH83BUNL/arcgis/rest/services/MiFlora_2019_0320/FeatureServer/0";
let layerCountyUrl = "https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_Counties/FeatureServer/0";
let screenWidth;
let view;
let map;
let currentFilter;
let baseURL = "https://lsa-miflora-p.lsait.lsa.umich.edu";
let familyBaseURL = baseURL + "/family/";
let genusBaseURL = baseURL + "/genus/";
let speciesBaseURL = baseURL + "/record/";
let specimenBaseURL = baseURL + "/specimen-record/";
let getHeaderExpr;

document.addEventListener('DOMContentLoaded', function () {
    screenWidth = window.innerWidth;
}, false);


window.onresize = function () {
    if (screenWidth !== window.innerWidth) {
        //console.log("Resizing. Saved width: " + screenWidth + " New width: " + window.innerWidth);
        screenWidth = window.innerWidth;
    }
};
require([
        "esri/portal/Portal",
        "esri/identity/IdentityManager",
        "esri/Map",
        "esri/views/MapView",
        "esri/layers/MapImageLayer",
        "esri/widgets/Search",
        "esri/layers/FeatureLayer",
        "esri/WebMap",
        "esri/Graphic",
        "esri/widgets/Legend",
        "esri/PopupTemplate",
        "esri/tasks/support/Query",

        "dojo/dom-style",
        "dojo/dom-attr",
        "dojo/on",
        "dojo/dom",
        "dojo/domReady!"
    ], function (
    Portal, esriId, Map, MapView, MapImageLayer, Search, FeatureLayer, WebMap, Graphic, Legend, Expand, PopupTemplate, Query, domStyle, domAttr, on, dom) {
        // ArcGIS Enterprise Portals are also supported
        var portal = new Portal();
        portal.load().then(function () {
            let layerLookup = new FeatureLayer({
                url: layerLookupItemUrl,
                visible: false
            });
            let query = layerLookup.createQuery();
            query.outFields = "FloraLayerID";
            query.where = "1=1";
            layerLookup.queryFeatures(query)
                .then(function(response){
                    layerAllUrl = response.features[0].attributes.FloraLayerId;
                    layerPointsUrl = layerAllUrl;
                    displayMap();
                })
        });
        function displayMap() {
            map = new Map({
                basemap: "topo"
            });
            let minZoom = 7;
            //Allow the user to zoom out farther on a smaller screen
            if(window.innerWidth<=380 || window.innerHeight<=450){
                minZoom = 5;
            }else if(window.innerWidth <= 800 || window.innerHeight <= 850){
                minZoom = 6;
            }
            view = new MapView({
                container: "map-section",
                map: map,
                center: [-84.69, 44.7], // lon, lat
                scale: 7000000,
                constraints: {
                    minZoom: minZoom,
                    maxZoom: 21,
                    snapToZoom: true,
                    rotationEnabled: false
                }

            });

            view.on("click", function (event) {
                // Search for graphics at the clicked location. View events can be used
                // as screen locations as they expose an x,y coordinate that conforms
                // to the ScreenPoint definition.
                view.hitTest(event).then(function (response) {
                    if (response.results.length===1 &&
                        response.results[0].graphic.hasOwnProperty("attributes") &&
                        response.results[0].graphic.layer.url.includes("Counties") ) {
                        //console.log(response);
                        // If there's a single result in response and it's a county (its layer has 'counties' in
                        // the name)), then show the county popups (points that have location by county centroid)
                        showCountyPopups(view.toMap(event));
                    }
                });
            });
            /*
            view.on("click", function(event) {
                // Find the geometry of the county clicked on
                let clickPt = view.toMap(event);
                showCountyPopups(clickPt);
            });*/

            let physDisp = function (value, key, data) {
                let physStr = "";
                if (value) {
                    physStr = "Phys: " + value;
                }
                return physStr;
            };

            let nativeDisp = function (value, key, data) {
                let nativeStr = "";
                if (value === "N") {
                    nativeStr = "Native"
                } else if (value === "A") {
                    nativeStr = "Adventive";
                    return nativeStr;
                }
            };

            let speciesURL = function (value, key, data) {
                let specUrl = "";
                if (value) {
                    specUrl = speciesBaseURL + value;
                }
                return specUrl
            };

            getHeaderExpr = function(value,key,data){
                let textStr = "Put this in the popup " + value;
                return textStr;
                //return getRecordHeader(data);
            };

            let countyPopup = {
                title: "{NAME} County"
            };

            let specimenPopup = new PopupTemplate({
                //title: "Species: {species1}", //getRecordHeader($feature),
                actions: [],
                content: [
                    {
                        type: "text",
                        text:"<font face=\"Tahoma\"><b><i>" +
                            "<a href=\"{expression/GenusURL}\" target=\"_blank\">{genus1}</a> "+
                            "<a href=\"{expression/SpeciesURL}\" target=\"_blank\">{species1}</a> {expression/subSpecies}" +
                            "</i></b> - <a href=\"{expression/FamilyURL}\" target=\"_blank\">{family1}</a> {expression/commonName}" +
                            "<br />{expression/collector}\n" +
                            "<br />{expression/county}{expression/sensitiveLocation}</font>\n" +
                            "<br /><b>{expression/catalog} </b>\n"
                   }],
                expressionInfos: [{
                    name: "phys",
                    title: "Phys",
                    expression: "IIf(IsEmpty($feature.phys), \"\", \"Phys: \" + $feature.phys)"
                }, {
                    name: "subSpecies",
                    title: "Plant Species",
                    expression: "When(!IsEmpty($feature.subspecies1), \" subsp. \" + $feature.subspecies1, \"\") " +
                        " + When(!IsEmpty($feature.variety1), \" var. \" + $feature.variety1, \"\") " +
                        " + When(!IsEmpty($feature.forma1), \" f. \" + $feature.forma1, \"\")"
                }, {
                   name: "commonName",
                   title: "Common Name",
                   expression: "When(!IsEmpty($feature.common_name), ' (' + $feature.common_name + ')','')"
                }, {
                    name: "nativeadv",
                    title: "Native/Adventive",
                    expression: "IIf($feature.na==\"N\", \"Native\", IIf($feature.na==\"A\", \"Adventive\",\"\"))"
                }, {
                    name: "county",
                    title: "County",
                    expression: "$feature.country + \", \" + $feature.state + IIf(IsEmpty($feature.county), \"\", \", \" + $feature.county + \" County\")"
                }, {
                    name: "sensitiveLocation",
                    title: "Location",
                    expression: "IIf($feature.sensitive==1, \": Exact localities for State and Federally listed rare plants not displayed\", " +
                        "IIf(Left($feature.LocalityName, 20) == \"Locality placeholder\", \"\", \": \" + $feature.LocalityName) + " +
                        "IIf(!IsEmpty($feature.township), \" T\" + $feature.township, \"\") + " +
                        "Iif(!IsEmpty($feature.range), \" R\" + $feature.range, \"\") + " +
                        "IIf(!IsEmpty($feature.section), \" Sec \" + $feature.section, \"\") + " +
                        "IIf(!IsEmpty($feature.sectionpart), \", \" + $feature.sectionpart, \"\") + " +
                        "IIf(!IsEmpty($feature.minelevation) || !IsEmpty($feature.maxelevation), \"; elev. \" + $feature.minelevation + IIf(!IsEmpty($feature.maxelevation), \" - \" + $feature.maxelevation,\"\") + \" \" + $feature.elevationunits,\"\") + " +
                        "IIf(!IsEmpty($feature.mindepth) || !IsEmpty($feature.maxdepth), \"; depth. \" + $feature.mindepth + IIf(!IsEmpty($feature.maxdepth), \" - \" + $feature.maxdepth,\"\") + \" \" + $feature.depthunits,\"\") " +
                        ")"
                }, {
                    name: "collected",
                    title: "Collection Information",
                    expression: "IIf(IsEmpty($feature.collectiondate) && IsEmpty($feature.collectors),\"\",\"Collected:\")"
                }, {
                    name: "collector",
                    title: "Collector Information",
                    expression: "IIf(!IsEmpty($feature.collectors), $feature.collectors + \" \" + IIf(!IsEmpty($feature.collectornumber), \", \" + $feature.collectornumber, \"\"), \"\")\n" +
                        " + IIf(!IsEmpty($feature.collectiondate), IIf(!Isempty($feature.collectors), \". Collected \", \"\") + $feature.collectiondate, \"\")"
                }, {
                    name: "catalog",
                    title: "Catalog Number",
                    expression: "IIf(Left($feature.catalognumber,1)==\"#\",\"\",\"MICH\" + $feature.catalognumber)"
                }, {
                    name: "FamilyURL",
                    title: "Family URL",
                    expression: "\"" + familyBaseURL + "\" + $feature.family1"
                }, {
                    name: "GenusURL",
                    title: "Genus URL",
                    expression: "\"" + genusBaseURL + "\" + $feature.genus1"
                }, {
                    name: "SpeciesURL",
                    title: "Species URL",
                    expression: "IIf(!IsEmpty($feature.plant_id), " + "\"" + speciesBaseURL + "\" + $feature.plant_id, \"\")"
                }]
            });

            let countyOutlineRenderer = {
                type: "simple",
                symbol: {
                    type: "simple-fill",
                    color: [0, 0, 0, 0],
                    outline: {
                        width: .5,
                        color: [190, 190, 190]
                    }
                }
            };

            let countyRenderer = {
                type: "simple",
                symbol: {
                    type: "simple-fill",
                    color: [229, 229, 229, .65],
                    outline: {
                        width: 1,
                        color: [214, 214, 214, 0]
                    }
                }
            };

            let specimenRenderer = {
                type: "unique-value",
                field: "locfromcounty",
                /*
                defaultSymbol: {
                    type: "simple-marker",
                    size: 8,
                    color: [76, 0, 115, .5],
                    outline: {
                        width: 0
                    }
                },*/
                legendOptions: {title: "Location from:"},
                uniqueValueInfos: [{
                    value: "False",
                    symbol: {
                        type: "simple-marker",
                        size: 8,
                        color: [56, 168, 0, 1],
                        outline: {width: 0}
                    },
                    label: "Specimen coordinates"
                }, {
                    value: "True",
                    symbol: {
                        type: "simple-marker",
                        size: 1,
                        color: [1, 1, 1, 0],
                        outline: {width: 0}
                    },
                    label: "County center"
                }]
            };
            //console.log("Renderers and popups done" );

            // Add the layers to the map.
            layer = new FeatureLayer({
                url: layerPointsUrl,
                visible: false,
                renderer: specimenRenderer,
                popupTemplate: specimenPopup
            });
            layerAll = new FeatureLayer({
                url: layerAllUrl,
                visible: false
            });
            countyLayer = new FeatureLayer({
                url: layerCountyUrl,
                visible: true,
                popupTemplate: countyPopup,
                popupEnabled: false,
                definitionExpression: "State_Name = 'Michigan'",
                renderer: countyRenderer
            });
            countyOutlineLayer = new FeatureLayer({
                url: layerCountyUrl,
                visible: true,
                popupTemplate: countyPopup,
                popupEnabled: false,
                definitionExpression: "State_Name = 'Michigan'",
                renderer: countyOutlineRenderer
            });
            map.add(countyOutlineLayer);
            map.add(countyLayer);
            map.add(layer);
            map.add(layerAll);

            view.when(function () {
                console.log("The view loaded.");
                // Do the initial search to filter the layer to only the default value.
                // This cuts down on the number of points initially loaded.
                doSearch();
                layer.visible=true;

                let legend = new Legend({
                    view: view,
                    layerInfos: [{
                        layer: layer,
                        //title: "Specimens"
                    }/*, {
                        layer: countyLayer,
                        title: "Counties"
                    }*/]
                });
                // Add widget to the bottom right corner of the view
                // Not necessary after all since there's no information for it.
                // view.ui.add(legend, "top-right");

            }, function (error) {
                console.log("The view's resources failed to load: ", error);
            });

        }

    }
);

function addToSql(sql, inputString, searchString) {
    //console.log("addToSql");
    if (inputString && inputString.length > 0) {
        if (inputString.constructor === Array) {
          // If there's only one item and it's empty, don't add anything.
          if (!(inputString.length === 1 && inputString[0].length === 0)) {
              sql = sql ? sql + " AND (" : "(";
              //console.log("initial: " + sql);
              //console.log("inputString: "+ inputString);
              for (let i of inputString) {
                //console.log("i: " + i);
                if (i.toUpperCase().includes("COUNTY")) {
                    i = i.toUpperCase().replace("COUNTY", "").trim();
                }
                sql = sql + searchString.replace('PLACEHOLDER', i.toUpperCase()) + " OR "
              }
              //console.log("SQL after inputString loop: " + sql);
              sql = sql.substr(0, sql.length - 4) + ")";
              //console.log("SQL after substr method: " + sql);
          }
      } else {
          sql += sql ? " AND " : "";
          //console.log("SQL when inputString is not an Array: " + sql);
          sql = sql + searchString.replace('PLACEHOLDER', inputString);
          //console.log("SQL + SearchString: " + sql);
      }
      //if(sql) {console.log({sql})}
    }
    return sql;
}

// Return an array of the selected option values
// select is an HTML select element
// From https://stackoverflow.com/questions/5866169/how-to-get-all-selected-values-of-a-multiple-select-box
function getSelectValues(select) {
    let result = [];
    let options = select && select.options;
    let opt;

    for (let i = 0, iLen = options.length; i < iLen; i++) {
        opt = options[i];

        if (opt.selected) {
            result.push(opt.value || opt.text);
        }
    }
    if (result.length === 0) {
        result = null;
    }
    return result;
}

function doSearch() {

    //console.log("doSearch()");
    //console.log(map);
    view.popup.close();
    //map.infoWindow.clearFeatures();
    let searchVal = decodeURI(window.location.search)
        .replace('?', '')
        .split('&')
        .map(param => param.split('='))
        .reduce((values, [ key, value ]) => {
            values[ key ] = value;
            return values
        }, {});
    //console.log(searchVal);

    let sql = "";
    if (searchVal.common_name){
        sql = addToSql(sql, searchVal.common_name, "UPPER(common_name) LIKE '%" + searchVal.common_name.toUpperCase() + "%'");
    }
    if(searchVal.family) {
        sql = addToSql(sql, searchVal.family, "UPPER(family1) LIKE '%" + searchVal.family.toUpperCase() + "%'");
    }
    if(searchVal.scientific_name) {
        sql = addToSql(sql, searchVal.scientific_name, "(UPPER(species1) LIKE '%" + searchVal.scientific_name.toUpperCase() +
            "%' OR UPPER(sci_name) LIKE '%" + sciName.toUpperCase() + "%')");
    }
    if(searchVal.genus) {
        sql = addToSql(sql, searchVal.genus, "UPPER(genus1) LIKE '%" + searchVal.genus.toUpperCase() + "' ");
    }
    if(searchVal.county) {
        sql = addToSql(sql, searchVal.county, "UPPER(county) LIKE '%PLACEHOLDER%'");
    }
    if (searchVal.plant_id){
        sql = addToSql(sql, searchVal.plant_id, "plant_id = " + searchVal.plant_id);
    }
    //console.log(sql);
    if (sql) {
        //console.log("Updating layer definition expression: " + sql);
        // When searching the map, always only return points with locations, not sensitive
        // Also don't show points where location is from county centroid
        layer.definitionExpression = "(" + sql + ") AND (donotmap <> '1' AND lat_val Is Not Null AND lon_val Is Not Null) ";
        currentFilter = sql;
        //console.log(sql);
/*        layer.when(function () {
            updateResults(currentFilter);
        });
        */
        /* Now we also need to search the county layer and only show counties that are represented here. */
        // First query the layer for all unique counties

        let countyQuery = layer.createQuery();
        countyQuery.where = sql;
        countyQuery.returnDistinctValues = true;
        countyQuery.returnGeometry = false;
        countyQuery.outFields = "county";
        //console.log(countyQuery);
        layer.queryFeatures(countyQuery)
            .then(function(response){
                let countyList = [];
                response.features.forEach(item => countyList.push("'" + item.attributes.county + "'"));
                //console.log(countyList);
                let countySql = "NAME IN (" + countyList.join(",") + ") AND STATE_NAME LIKE 'Michigan'";
                //console.log(countySql);
                countyLayer.definitionExpression = countySql;
            })
            .catch(function(error){
                //console.log("Error encountered");
            })
    } else {
        //console.log("Sql string empty");
    }

}

function showCountyPopups(geomPt){
    // Find the counties that contain the current search specimens
    let query = countyLayer.createQuery();
    query.geometry = geomPt;  // the point location of the pointer
    query.spatialRelationship = "within";
    query.returnGeometry = true;
    query.returnCentroid = true;
    query.outFields = [ "NAME" ];

    countyLayer.queryFeatures(query)
        .then(function(response){
            // returns a feature set with features containing the
            // POPULATION attribute and each feature's geometry
            // And now query the feature layer for this geometry
            //console.log({response});
            query = layer.createQuery();
            //query.where = "locfromcounty LIKE 'True'";
            query.geometry = response.features[0].geometry;
            query.spatialRelationship = "contains";
            query.returnGeometry = true;
            // This seems to REPLACE the geometry filter instead of further refining it.
            //query.where = "locfromcounty LIKE 'True'";
            layer.queryFeatures(query)
                .then(function(response){
                    //console.log({response});
                    let selectedFeatures = [];
                    for(let fIdx = 0; fIdx<response.features.length; fIdx++) {
                       // console.log(response.features[fIdx].attributes);
                        //if (response.features[fIdx].attributes.locfromcounty === "True") {
                            selectedFeatures.push(response.features[fIdx]);
                        //}
                    }
                    goToFeature(selectedFeatures);
                })
        });

}
function goToFeature(selectedFeatures) {
    //selectedCounty.visible=false;
    // Thanks to this discussion thread: https://community.esri.com/thread/179494
    console.log("Go to feature");
    console.log(selectedFeatures);
     view.popup.open({
        features: selectedFeatures,
        location: selectedFeatures[0].geometry
    });
}

function getSpecimenCountyPopup(data) {
    //console.log(data);
    let specimenCountyPopup = {
        //title: getRecordHeader(data),
        content: [
            {
                type: "text",
                text: "<font face='Tahoma'\>" + getRecordHeader(data) + "\n" +
                    "<br />" + getCollected(data) +
                    "<br />" + getCounty(data) + getDetailedLocation(data) +
                    "<br />" + getCatalog(data)+ " <br /> </font>\n"
            }]
    };
    return specimenCountyPopup;
}

function getRecordHeader(data) {
    let family = (data.family1) ? data.family1 : "Unknown Family";
    let genus = (data.genus1) ? data.genus1 : "Unknown Genus";
    let species = data.species1 ? data.species1 : "Unknown Species";
    let speciesURL = getSpeciesURL(data.plant_id, species);
    let familyURL = getFamilyURL(family);
    let genusURL = getGenusURL(genus);
    let fullname = "<b><i>" + genusURL + " " + speciesURL + "</b></i>";
    if (data.subspecies1) {
        fullname += ' subsp. ' + data.subspecies1;
    }
    if (data.variety1) {
        fullname += ' var. ' + data.variety1;
    }
    if (data.forma1) {
        fullname += 'f. ' + data.forma1;
    }
    fullname += ' - ' + familyURL + ' (' + data.common_name + ')';
    return fullname
}
function getNonSensitiveInfo(data){
    if( data.sensitive === "1" || data.sensitive === 1){
        return " "
    } else {
        return getDetailedLocation(data) + "<br />" +  getCollected(data) + "<br />\n";
    }
}
function getCatalog(data) {
    if(data.catalognumber[0] === "#") {
        return "";
    } else {
        return "<b>MICH" + data.catalognumber + "</b>";
    }
}

function getDetailedLocation(data) {
    //console.log(data.localityname.includes('Locality placeholder'));
    if (data.sensitive === 1 || data.sensitive === 1) {
        return ": Exact localities for State and Federally listed rare plants not displayed."
    } else {
        let locStr = ": ";
        if (data.localityname !== null) {
            locStr += (data.localityname.includes('Locality placeholder') ? "" : data.localityname);
        };
        locStr += data.township ? " T" + data.township : "";
        locStr += data.range ? " R" + data.range : "";
        locStr += data.section? " Sec" + data.section : "";
        locStr += data.sectionpart? " " + data.sectionpart : "";
        locStr += data.minelevation || data.maxelevation ? "; elev. " + data.minelevation + (data.maxelevation && data.minelevation ? " - " : "") + data.maxelevation + " " + data.elevationunits : "";
        locStr += data.mindepth || data.maxdepth? "; depth " + data.mindepth + (data.mindepth && data.maxdepth ? " - " : "") + data.maxdepth + " " + data.depthunits : "";
        return locStr;
    }
}

function getCollected(data){
    let collectors = data.collectors;
    let collectionDate = data.collectiondate;
    let endDate = data.collectionenddate;
    let collectorNum = data.collectornumber;
    let collectionStr = "";
    if (collectionDate || collectors) {
        collectionStr = collectors && data.sensitive!=="1" ? collectionStr + collectors + (collectorNum ? ', ' + collectorNum : "") : collectionStr;
        collectionStr = collectionDate && collectors && data.sensitive!=="1" ? collectionStr + '. ' : collectionStr;
        collectionStr = collectionDate ? collectionStr + 'Collected: ' + collectionDate : collectionStr;
        collectionStr = endDate ? collectionStr + ' - ' + endDate : collectionStr;
    }
    return collectionStr;
}
function getCounty(data) {
    let county = data.county;
    return data.country + ", " + data.state + ", " + (county ? county + " County" : "");
}
function getNativeAdv(na) {
    return na==="N" ? "Native" : na==="A"? "Adventive" : "";
}
function getPhys(phys) {
    return phys ? "Phys: " + phys : "";
}

function makeURLText(url, text) {
    return url ? '<a href="' + url + '" target="_blank">' + text + "</a>" : text;
}

function getSpeciesURL(plantid, species){
    let url = "<a href=\"" + speciesBaseURL + plantid +"\" target=\"_blank\">" + species + "</a>\n</b>";
    console.log(url);
    if(plantid) {
        return url;
    }
    else {
        return species + "\n</b>";
    }
}
function getFamilyURL(family) {
    return  "<a href=\"" + familyBaseURL + family + "\" target=\"_blank\">" + family + "</a>\n";
}
function getGenusURL(genus) {
    return "<a href=\"" + genusBaseURL + genus + "\" target=\"_blank\">" + genus + "</a>\n";
}
