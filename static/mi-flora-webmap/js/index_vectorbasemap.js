let layer;
let layerAll;
let countyLayer;
let mapId = "29bdfa406ed9418ab3173ba5612737bd"; //"7a4ba6af54584998a4779df35925e025"; // MiFloraMar2019  "72fcc1b39d9a4bd59610ffa2bdc0ada3"; // This is the "MiFloraMap01" item
let layerId = "MiFlora_2019_0320_Locations_2595"; //"MiFloraMar2019Locations_5347"; //"SpecifyJoinMiFlora_20190215_WithLocations_2976"; // "SpecimensWithLocationAndMiFlora_7827"; //"SpecimensWithLocation_NonSensitive_4343";
let layerAllId = "MiFlora_2019_0320_4369"; //"MiFloraMar2019_8121"; //"SpecifyJoinMiFlora_20190215_4899";
let layerPointsUrl = "https://services1.arcgis.com/4ezfu5dIwH83BUNL/arcgis/rest/services/MiFlora_2019_0403/FeatureServer/0" //https://services1.arcgis.com/4ezfu5dIwH83BUNL/arcgis/rest/services/MiFlora_2019_0320_Locations/FeatureServer/0";
let layerAllUrl = "https://services1.arcgis.com/4ezfu5dIwH83BUNL/arcgis/rest/services/MiFlora_2019_0403/FeatureServer/0" //https://services1.arcgis.com/4ezfu5dIwH83BUNL/arcgis/rest/services/MiFlora_2019_0320/FeatureServer/0";
let layerCountyUrl = "https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_Counties/FeatureServer/0";
//let layerId2 = "SpecimensWithLocation_NonSensitive_4343"; // Just testing. The layer can be found on the map even if it's not visible.
let countyLayerId = "USA_Counties_5470"; //"USA_Counties_9498"; //"USA_Counties_5955";
let screenWidth;
let view;
let map;
let selectedCounty;
let currentFilter;
let defaultField = "scientific_name";  //"ScientificName"; "Collectors"
let defaultVal = "Acer rubrum";  //"mimulus"; //"leisman"; //"Acer rubrum";
let familyBaseURL = "https://michiganflora.net/family.aspx?id=";
let genusBaseURL = "https://michiganflora.net/genus.aspx?id=";
let speciesBaseURL = "https://michiganflora.net/species.aspx?id=";
let getHeaderExpr;
let modal;

document.addEventListener('DOMContentLoaded', function () {
    screenWidth = window.innerWidth;
    document.getElementById("sci-name").value = defaultVal;
    modal = document.getElementById("search-hints");

}, false);


window.onresize = function () {
    if (screenWidth !== window.innerWidth) {
        //console.log("Resizing. Saved width: " + screenWidth + " New width: " + window.innerWidth);
        resize();
        screenWidth = window.innerWidth;
    }
};
require([
        "esri/portal/Portal",
        "esri/identity/OAuthInfo",
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
        "esri/Basemap",
        "esri/layers/VectorTileLayer",

        "dojo/dom-style",
        "dojo/dom-attr",
        "dojo/on",
        "dojo/dom",
        "dojox/form/RangeSlider",
        "dojo/domReady!"
    ], function (
    Portal, OAuthInfo, esriId, Map, MapView, MapImageLayer, Search, FeatureLayer, WebMap, Graphic, Legend, PopupTemplate,
    Basemap, VectorTileLayer,
    domStyle, domAttr, on, dom) {
        // ArcGIS Enterprise Portals are also supported
        var portalUrl = "https://www.arcgis.com/sharing";
        // substitute your own client_id to identify who spawned the login and check for a matching redirect URI
        var info = new OAuthInfo({
            appId: "x2yb7nNC233dm0I6",
            popup: false // inline redirects don't require any additional app configuration
        });
        esriId.registerOAuthInfos([info]);

        // send users to arcgis.com to login
        on(dom.byId("sign-in"), "click", function () {
            esriId.getCredential(portalUrl);
        });

        // log out and reload
        on(dom.byId("sign-out"), "click", function () {
            esriId.destroyCredentials();
            window.location.reload();
        });

        // persist logins when the page is refreshed
        esriId.checkSignInStatus(portalUrl).then(
            function () {
                dom.byId('anonymousPanel').style.display = 'none';
                dom.byId('personalizedPanel').style.display = 'none';

                // display the map once the user is logged in
                displayMap();
            }
        );

        var darkGrayStyleURL = "https://www.arcgis.com/sharing/rest/content/items/57436c01bc754dbb87dfb636b6484022/resources/styles/root.json";
        var lightGrayStyleURL = "https://www.arcgis.com/sharing/rest/content/items/1e47168d181248e491541ffd5a91c0de/resources/styles/root.json"


        var vector_basemap = new Basemap({
            baseLayers: [
                new VectorTileLayer({
                    portalItem: {
                        id: "b99819fdf231408a90956bbca30ce5d3" // Forest and Parks Canvas
                    }
                })
            ]
        });

        function displayMap() {
            var portal = new Portal();
            console.log("displayMap()");
            // Once the portal has loaded, the user is signed in
            portal.load().then(function () {
                map = new Map({
                    basemap: vector_basemap
                });


                view = new MapView({
                    container: "map-section",
                    map: map,
                    center: [-84.69, 44.7], // lon, lat
                    scale: 7000000
                });

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
                                "<br /><b>{expression/catalog}??</b>\n"
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

                let countyRenderer = {
                    type: "simple",
                    symbol: {
                        type: "simple-fill",
                        color: [229, 229, 229, .6],
                        outline: {
                            width: 1,
                            color: [214, 214, 214, .6]
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
                            color: [56, 168, 0, .5],
                            outline: {width: 0}
                        },
                        label: "Specimen coordinates"
                    }, {
                        value: "True",
                        symbol: {
                            type: "simple-marker",
                            size: 8,
                            color: [20, 158, 206, .5],
                            outline: {width: 0}
                        },
                        label: "County center"
                    }]
                };
                console.log("Renderers and popups done" );

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
                    view.ui.add(legend, "bottom-right");

                    /* Don't update when moving/zooming the map after all.
                    view.whenLayerView(layer).then(function (layerView) {
                        // This happens any time the layer view is updated and finishes loading.
                        console.log("watching for updates...");
                        layerView.watch("updating", function (value) {
                            console.log("watching...");
                            if (!value) { // wait for the layer view to finish updating
                                console.log("updates done");
                                // query all the features available for drawing.
                                /* This only queries the current view
                                layerView.queryFeatures({
                                    geometry: view.extent,
                                    returnGeometry: true})
                                    */
                    /*
                                let queryAll = layerAll.createQuery();
                                queryAll.orderByFields = ['family1', 'genus1', 'species1'];
                                queryAll.where = currentFilter;
                                queryAll.outFields = ["*"];
                                layerAll.queryFeatures(queryAll)
                                    .then(function (allResults) {
                                        let resultText = " of " + allResults.features.length + " specimens found with coordinates. ";
                                        createTable(allResults.features.slice(0, 2000));
                                        let queryLoc = layer.createQuery();
                                        queryLoc.where = layer.definitionExpression;
                                        console.log(queryLoc.where);
                                        queryLoc.outFields = ["*"];
                                        queryLoc.returnGeometry = false;
                                        layer.queryFeatures(queryLoc).then(function (locResults) {
                                            console.log("locResults");
                                            console.log(locResults);
                                            resultText = locResults.features.length + resultText;
                                            if (locResults.features.length >= 2000) {
                                                resultText = resultText + " Mapping first 2000 specimens.";
                                            }
                                            document.getElementById("result-count").innerText = resultText;
                                        })
                                        /*
                                        let resultText = results.features.length + " specimens found";
                                        if (results.features.length >= 2000) {
                                            resultText = resultText + " . Displaying first 2000.";
                                        }
                                        document.getElementById("result-count").innerText = resultText;
                                        console.log("view.whenLayerView");
                                        createTable(results.features.slice(0,2000));
                                        */
                    /*
                                    }).catch(function (error) {
                                    console.error("query failed: ", error);
                                });
                            } else {
                                console.log("updating...");
                                //clearResultText();
                            }
                        });
                    });
*/
                    //updateResultText();
                }, function (error) {
                    console.log("The view's resources failed to load: ", error);
                })
            });
        }

    }
);

function addToSql(sql, inputString, searchString) {
    console.log("addToSql");
    if (inputString && inputString.length > 0) {
        if (inputString.constructor === Array) {
            // If there's only one item and it's empty, don't add anything.
            if (!(inputString.length === 1 && inputString[0].length === 0)) {
                sql = sql ? sql + " AND (" : "(";
                for (let i of inputString) {
                    if (i.includes("county")) {
                        i = i.toUpperCase().replace(" COUNTY", "");
                    }
                    sql = sql + searchString.replace('PLACEHOLDER', i.toUpperCase) + " OR "
                }
                sql = sql.substr(0, sql.length - 4) + ")";
            }
        } else {
            sql += sql ? " AND " : "";
            sql = sql + searchString.replace('PLACEHOLDER', inputString);
        }
        if(sql) {console.log({sql})};
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
    console.log("doSearch()");
    console.log(map);
    view.popup.close();
    //map.infoWindow.clearFeatures();
    let commonName = document.getElementById("common-name").value;
    let sciName = document.getElementById("sci-name").value;
    let genus = document.getElementById("genus").value;
    let family = document.getElementById("family").value;
    /*
    let nativeAdv = document.getElementById("native-adv").value;
    let c = document.getElementById("c").value;
    let wetness = getSelectValues(document.getElementById("wetness"));
    let phys = getSelectValues(document.getElementById("phys"));
    let stateStat = getSelectValues(document.getElementById("state-stat"));
    */
    let collectorName = document.getElementById("collector-name").value.toUpperCase();
    let collectorNum = document.getElementById("collector-num").value;
    let collectionYear = document.getElementById("collection-year").value;
    let loc = document.getElementById("location").value.toUpperCase();
    let county = getSelectValues(document.getElementById("county"));

    let sql = "";
    sql = addToSql(sql, commonName, "UPPER(common_name) LIKE '%" + commonName.toUpperCase() + "%'");
    sql = addToSql(sql, family, "UPPER(family1) LIKE '%" + family.toUpperCase() + "%'");
    sql = addToSql(sql, sciName, "UPPER(species1) LIKE '%" + sciName.toUpperCase() +
        "%' OR UPPER(scientific_name) LIKE '%" + sciName.toUpperCase() + "%'");
    sql = addToSql(sql, genus, "UPPER(genus1) LIKE '%" + genus.toUpperCase() + "' ");
    sql = addToSql(sql, county, "UPPER(county) LIKE '%PLACEHOLDER%'");
    sql = addToSql(sql, loc, "UPPER(localityname) LIKE '%PLACEHOLDER%'");
    sql = addToSql(sql, collectorName, "UPPER(collectors) LIKE '%PLACEHOLDER%'");
    sql = addToSql(sql, collectionYear, "collectiondate LIKE '%PLACEHOLDER%'");
    sql = addToSql(sql, collectorNum, "collectornumber LIKE 'PLACEHOLDER'");
    /*
    sql = addToSql(sql, nativeAdv, "UPPER(NA) LIKE '%" + nativeAdv + "%'");
    sql = addToSql(sql, loc, "UPPER(County) LIKE '%PLACEHOLDER%'");
    sql = addToSql(sql, c, "C LIKE 'PLACEHOLDER'");
    sql = addToSql(sql, wetness, "WET LIKE 'PLACEHOLDER'");
    sql = addToSql(sql, phys, "PHYS LIKE 'PLACEHOLDER'");
    sql = addToSql(sql, stateStat, "ST LIKE 'PLACEHOLDER'");
    */
    //console.log(sql ? sql : "No search parameters");
    if (sql) {
        clearResultText();
        console.log("Updating layer definition expression: " + sql);
        // When searching the map, always only return points with locations, not sensitive
        layer.definitionExpression = "(" + sql + ") AND (donotmap <> '1' AND LatVal Is Not Null AND LonVal Is Not Null)";
        currentFilter = sql;
        updateResults(currentFilter);
/*        layer.when(function () {
            updateResults(currentFilter);
        });
        */
        console.log("doSearch complete");
    } else {
        console.log("sql string was empty");
    }

}

function updateResults(currentFilter) {
    // Query the table of all records (including those without location info) for table display
    console.log("updateResults: " + currentFilter);
    let queryAll = layerAll.createQuery();
    queryAll.orderByFields = ['family1', 'genus1', 'species1'];
    queryAll.where = currentFilter;
    queryAll.outFields = ["*"];
    queryAll.maxRecordCountFactor = 5;
    layerAll.queryFeatures(queryAll)
    .then(function (allResults) {
        let allCount = allResults.features.length;
        if (allCount===0) {
            resultText = "No results found."
            document.getElementById("result-count").innerText = resultText;
        }
        else {
            let resultText = allCount + " specimens found. ";
            createTable(allResults.features.slice(0, 2000));
            //let queryLoc = layer.createQuery(); //this already respects the definition expression.
            //queryLoc.where = layer.definitionExpression;
            //console.log(queryLoc.where);
            //queryLoc.outFields = ["catalognumber"];
            //queryLoc.returnGeometry = false;
            layer.queryFeatureCount().then(function (resultCount) {
                resultText = resultText + resultCount + ' specimens have collection location coordinates and are displayed on the map.';
                if (resultCount >= 2000) {
                    resultText = resultText + " Mapping first 2000 specimens.";
                }
                document.getElementById("result-count").innerText = resultText;
            });
        }
        //createTable(allResults.features.slice(0,2000));
    })
    .catch(function (error) {
        console.error("query failed: ", error);
    });

}

function clearSearch() {
    document.getElementById("search-form").reset();

}

function clearResultText() {
    document.getElementById("result-count").innerText = "Loading Specimens...";
    createTable([]);
}

function makeURLText(url, text) {
    return url ? '<a href="' + url + '" target="_blank">' + text + "</a>" : text;
}

//From https://stackoverflow.com/questions/15164655/generate-html-table-from-2d-javascript-array
function createTable(tableData) {
    var table = document.getElementById('result-table');
    var old_tableBody = document.getElementById('result-rows');
    var new_tableBody = document.createElement('tbody');
    new_tableBody.id = 'result-rows';
    console.log("createTable()");
    //console.log(tableData);
    let x = 0;

    tableData.forEach(function (rowData) {
        x += 1;
        //console.log(rowData.attributes);
        //console.log(rowData);
        let collectedBy = getCollected(rowData.attributes);
        let locationInfo = getCounty(rowData.attributes) + getDetailedLocation(rowData.attributes);
        let catalogNumber = getCatalog(rowData.attributes);
        var row = document.createElement('tr');
        row.className = "title-row action";
        var cell = document.createElement('td');
        let clickFunction;

        cell.innerHTML = getRecordHeader(rowData.attributes);
        //console.log(rowData.geometry.x , rowData.geometry.y);
        cell.className = "title-cell";
        if (rowData.attributes.donontmap === "1") {
            clickFunction = null;
        } else {
            clickFunction = function() { goToFeature(rowData)};
        }
        cell.onclick = clickFunction;
        row.appendChild(cell);
        new_tableBody.appendChild(row);

        if (collectedBy) {
            row = document.createElement('tr');
            row.className = "collection-row";
            cell = document.createElement('td');
            cell.innerHTML = collectedBy;

            cell.onclick = clickFunction;
            row.appendChild(cell);
            new_tableBody.appendChild(row);
        }

        if (locationInfo) {
            row = document.createElement('tr');
            row.className = "location-row";
            cell = document.createElement('td');
            cell.innerHTML = locationInfo;
            cell.onclick = clickFunction;
            row.appendChild(cell);
            new_tableBody.appendChild(row);
        }

        if (catalogNumber) {
            row = document.createElement('tr');
            row.className = "catalog-row";
            cell = document.createElement('td');
            cell.innerHTML = catalogNumber;
            cell.onclick = clickFunction;
            row.appendChild(cell);
            new_tableBody.appendChild(row);
        }

        row = document.createElement('tr');
        row.className = "full-record-row";
        cell=document.createElement('td');
        cell.innerHTML = '<a href="comingsoon.html" target="_blank">View Full Record</a>';
        cell.onclick = clickFunction;
        row.appendChild(cell);
        new_tableBody.appendChild(row);

    });
    old_tableBody.parentNode.replaceChild(new_tableBody, old_tableBody);
    //table.appendChild(tableBody);
    // document.body.appendChild(table);
}

function goToFeature(selectedFeature) {
    //selectedCounty.visible=false;
    // Thanks to this discussion thread: https://community.esri.com/thread/179494
    //console.log(selectedFeature.attributes);
    // If there are no lat/lon coordinates, but there is a county, and it's not marked do not map, only show the count
    if ((!selectedFeature.attributes.LatVal || !selectedFeature.attributes.LonVal) &&
        selectedFeature.attributes.county &&
        selectedFeature.attributes.donotmap!=="1" && selectedFeature.attributes.donotmap!==1) {
        // Only show the county
        var query = countyLayer.createQuery();
        // query.geometry = (selectedFeature.geometry);  // the point location of the pointer
        // query.spatialRelationship = "intersects";  // this is the default
        // query.returnGeometry = true;
        query.where = "UPPER(NAME) LIKE '" + selectedFeature.attributes.county.toUpperCase() +
            "' AND UPPER(STATE_NAME)='MICHIGAN'";
        // query.outFields = [ "NAME" ]; This keeps the popup.open function from having sufficient information to highlight the feature
        // It needs the FID field as well.

        countyLayer.queryFeatures(query)
            .then(function (response) {
                console.log("countyLayer query response:");
                console.log(response);
                let featureCounty = response.features[0];
                console.log({featureCounty});
                /*
                selectedCounty.geometry = featureCounty.geometry;
                selectedCounty.attributes = featureCounty.attributes;
                selectedCounty.visible = true;
                console.log("Selected county:");
                console.log(selectedCounty);
                */
                // Set the county popup to show the specimen information for the selected specimen.
                // This shouldn't be a problem since we've turned off the ability to click a county to see the popup.
               countyLayer.popupTemplate = getSpecimenCountyPopup(selectedFeature.attributes);
               countyLayer.popupEnabled=true;
                view.popup.open({
                    features: [featureCounty],
                    location: featureCounty.geometry.centroid
                });
                view.center = featureCounty.geometry.centroid;
                countyLayer.popupEnabled=false;
            });

    } else if (selectedFeature.attributes.LatVal && selectedFeature.attributes.LonVal &&
        selectedFeature.attributes.donotmap!=="1" && selectedFeature.attributes.donotmap!==1) {
        //Otherwise, as long as has coordinates and isn't marked do not map, show its popup
        var query = layer.createQuery();
        query.where = "catalognumber LIKE '" + selectedFeature.attributes.catalognumber + "'";
        /*
        query.geometry = selectedFeature.geometry;
        query.spatialRelationship = "intersects";
        */
        layer.queryFeatures(query)
            .then(function(response){
                let mapFeature = response.features[0];
                //console.log(mapFeature);
                view.popup.open({
                    features: [mapFeature],
                    location: mapFeature.geometry
                });
                view.center = mapFeature.geometry;

            })
    }
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
                    "<br />" + getCatalog(data)+ "??<br />??</font>\n"
            }]
    };
    return specimenCountyPopup;
}

function getRecordHeader(data) {
    let family = (data.family1) ? data.family1 : "Unknown Family";
    let genus = (data.genus1) ? data.genus1 : "Unknown Genus";
    let species = data.species1 ? data.species1 : "Unknown Species";
    let speciesURL = makeURLText(data.speciesurl, species);
    let familyURL = makeURLText(data.familyurl, family);
    let genusURL = makeURLText(data.genusurl, genus);
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
        let locStr = ": " + (data.localityname.includes('Locality placeholder') ? "" : data.localityname);
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

function showHints() {
    modal.style.display="block";
}

function hideHints() {
    modal.style.display = "none";
}
window.onclick = function(event) {
    if (event.target === modal) {
        modal.style.display = "none";
    }
}
function showSearch() {
    //document.getElementById("")
    document.getElementById("search-tools").style.display = "grid";
    document.getElementById("page-grid").style.gridTemplateRows = "auto 5vh";
    document.getElementById("search-section-label").innerHTML = "Hide Search Options";
    document.getElementById("map-section").style.display = "none";
    document.getElementById("results-section").style.display = "none";
    document.getElementById("search-section-label").setAttribute("onclick", "hideSearch();");
}

function hideSearch() {
    //document.getElementById("")
    document.getElementById("search-tools").style.display = "none";
    document.getElementById("page-grid").style.gridTemplateRows = "4vh 87vh 4vh 5vh";
    document.getElementById("map-section").style.display = "flex";
    document.getElementById("results-section").style.display = "block";
    document.getElementById("search-section-label").innerHTML = "Show Search Options";
    document.getElementById("search-section-label").setAttribute("onclick", "showSearch();");
}

function showResults() {
    console.log("Showing results");
    document.getElementById("results-contents").style.display = "grid";
    document.getElementById("page-grid").style.gridTemplateRows = "0 44vh 43vh 3vh";
    document.getElementById("results-section-label").innerHTML = "Hide Results Table";
    document.getElementById("results-section-label").setAttribute("onclick", "hideResults();");
}

function hideResults() {
    console.log("Hiding results");
    document.getElementById("results-contents").style.display = "none";
    document.getElementById("page-grid").style.gridTemplateRows = "4vh 87vh 4vh 5vh";
    document.getElementById("results-section-label").innerHTML = "Show Results Table";
    document.getElementById("results-section-label").setAttribute("onclick", "showResults();");
}

function resize() {
    console.log(window.innerWidth);
    if (window.innerWidth >= 700) {
        document.getElementById("page-grid").style.gridTemplateRows = " 70vh 26vh 4vh";
        document.getElementById("page-grid").style.gridTemplateColumns = "300px 1fr";
        document.getElementById("results-contents").style.display = "grid";
        document.getElementById("search-tools").style.display = "grid";
    } else {
        document.getElementById("page-grid").style.gridTemplateColumns = "100vw";
        hideSearch();
        hideResults();
    }
}