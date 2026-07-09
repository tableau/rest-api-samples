// Copyright (c) 2016 Tableau. Licensed under the MIT License.
// SPDX-License-Identifier: MIT
package com.tableausoftware.documentation.api.rest.bindings;

import java.util.ArrayList;
import java.util.List;
import jakarta.xml.bind.annotation.XmlAccessType;
import jakarta.xml.bind.annotation.XmlAccessorType;
import jakarta.xml.bind.annotation.XmlType;

@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "viewListType", propOrder = { "view" })
public class ViewListType {

    protected List<ViewType> view;

    public List<ViewType> getView() {
        if (view == null) {
            view = new ArrayList<>();
        }
        return this.view;
    }
}
