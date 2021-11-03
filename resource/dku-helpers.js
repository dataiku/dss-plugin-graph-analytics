/*
Helper function to query webapp backend with a default implementation for error handling
v 1.0.1
*/

function checkMandatoryParameters(param, webAppConfig) {
    if (param.mandatory) {
        var val = webAppConfig[param.name];
        if (val == undefined || val == "") {
            throw new Error("Mandatory column '" + param.name + "' not specified.");
        }
    }
}

function checkWebAppParameters(webAppConfig, webAppDesc) {
    if (webAppDesc.topBarParams) {
        webAppDesc.topBarParams.forEach(p => {checkMandatoryParameters(p, webAppConfig)});
    }
    if (webAppDesc.leftBarParams) {
        webAppDesc.leftBarParams.forEach(p => {checkMandatoryParameters(p, webAppConfig)});
    }
};

function checkWebAppConfig(webAppConfig) {
    if (webAppConfig['source'] == webAppConfig['target']) {
        throw Error("Columns must be different")
    }
}

function quadraticScalingFunction(min, max, total, value) {
    if (max === min) {
        return 0;
    } else {
        var scale = 1 / (max - min);
        return Math.pow(Math.max(0,(value - min)*scale), 2);
    }
}

function isEqual(object1, object2) {
    return JSON.stringify(object1) == JSON.stringify(object2)
}


dataiku.webappBackend = (function() {
    function getUrl(path) {
        return dataiku.getWebAppBackendUrl(path);
    }

    function dkuDisplayError(error) {
        console.warn("backend error: ", error);
    }

    function post(path, args = {}, displayErrors = true) {
        return fetch(getUrl(path), {
            method: 'POST',
            body: JSON.stringify(args)
        })
        .then(response => {
            if (response.status == 502) {
                throw Error("Webapp backend not started");
            } else if (!response.ok) {
                response.text().then(text => dataiku.webappMessages.displayFatalError(`Backend error:\n${text}.\nCheck backend log for more information.`))
                throw Error("Response not ok!")
            } 
            try {
                return response.json();
            } catch {
                throw Error('The backend response is not JSON: '+ response.text());
            }
        })
        .catch(function(error) {
            if (displayErrors && error.message && !error.message.includes('not started')) { // little hack, backend not started should be handled elsewhere
                dataiku.webappMessages.displayFatalError(error)
            }
            throw error;
        });
    }

    return Object.freeze({getUrl, post});
})();


dataiku.webappMessages = (function() {
    function displayFatalError(err) {
        const errElt = $('<div class="fatal-error" style="margin: 100px auto; text-align: center; color: var(--error-red)"></div>')
        errElt.text(err);
        $('#graph-chart').html(errElt);
    }
    return  Object.freeze({displayFatalError})
})();
