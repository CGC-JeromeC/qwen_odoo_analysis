/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState } from "@odoo/owl";

// Masked Field Component for Odoo Sign
class SignMaskedField extends Component {
    setup() {
        this.state = useState({ value: this.props.value || "", showValue: false });
    }

    onInput(ev) {
        const newValue = ev.target.value;
        this.state.value = newValue;
        if (this.props.update) {
            this.props.update(newValue);
        }
    }

    toggleVisibility() {
        this.state.showValue = !this.state.showValue;
    }

    get inputType() {
        return this.state.showValue ? "text" : "password";
    }
}

SignMaskedField.template = "cgc_sign_masked_field.SignMaskedField";
SignMaskedField.props = {
    value: { type: String, optional: true },
    update: { type: Function, optional: true },
};

// Register the masked field in the sign field registry
const signFieldRegistry = registry.category("sign_fields");

signFieldRegistry.add("masked", {
    component: SignMaskedField,
    supportedTypes: ["text"],
    extractValue: (element, field) => {
        const input = element.querySelector("input");
        return input ? input.value : "";
    },
    setValue: (element, value, field) => {
        const input = element.querySelector("input");
        if (input) {
            input.value = value;
        }
    },
    isDisplayed: (field) => {
        return field.field_type === 'masked';
    },
});
