// Copyright (c) 2016 Tableau. Licensed under the MIT License.
// SPDX-License-Identifier: MIT
package com.tableausoftware.documentation.api.rest.bindings;

import java.util.ArrayList;
import java.util.List;
import jakarta.xml.bind.annotation.XmlAccessType;
import jakarta.xml.bind.annotation.XmlAccessorType;
import jakarta.xml.bind.annotation.XmlType;

@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "siteListType", propOrder = { "site" })
public class SiteListType {

    protected List<SiteType> site;

    public List<SiteType> getSite() {
        if (site == null) {
            site = new ArrayList<>();
        }
        return this.site;
    }
}
