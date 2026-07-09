// Copyright (c) 2016 Tableau. Licensed under the MIT License.
// SPDX-License-Identifier: MIT
package com.tableausoftware.documentation.api.rest.bindings;

import java.util.ArrayList;
import java.util.List;
import jakarta.xml.bind.annotation.XmlAccessType;
import jakarta.xml.bind.annotation.XmlAccessorType;
import jakarta.xml.bind.annotation.XmlType;

@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "groupListType", propOrder = { "group" })
public class GroupListType {

    protected List<GroupType> group;

    public List<GroupType> getGroup() {
        if (group == null) {
            group = new ArrayList<>();
        }
        return this.group;
    }
}
