// Copyright (c) 2016 Tableau. Licensed under the MIT License.
// SPDX-License-Identifier: MIT
package com.tableausoftware.documentation.api.rest.bindings;

import java.util.ArrayList;
import java.util.List;
import jakarta.xml.bind.annotation.XmlAccessType;
import jakarta.xml.bind.annotation.XmlAccessorType;
import jakarta.xml.bind.annotation.XmlElement;
import jakarta.xml.bind.annotation.XmlType;

@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "granteeCapabilitiesType", propOrder = { "group", "user", "capabilities" })
public class GranteeCapabilitiesType {

    protected GroupType group;
    protected UserType user;
    @XmlElement(required = true)
    protected GranteeCapabilitiesType.Capabilities capabilities;

    public GroupType getGroup() { return group; }
    public void setGroup(GroupType value) { this.group = value; }
    public UserType getUser() { return user; }
    public void setUser(UserType value) { this.user = value; }
    public GranteeCapabilitiesType.Capabilities getCapabilities() { return capabilities; }
    public void setCapabilities(GranteeCapabilitiesType.Capabilities value) { this.capabilities = value; }

    @XmlAccessorType(XmlAccessType.FIELD)
    @XmlType(name = "", propOrder = { "capability" })
    public static class Capabilities {

        @XmlElement(required = true)
        protected List<CapabilityType> capability;

        public List<CapabilityType> getCapability() {
            if (capability == null) {
                capability = new ArrayList<>();
            }
            return this.capability;
        }
    }
}
