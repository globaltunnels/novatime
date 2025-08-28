
import type { Meta, StoryObj } from '@storybook/react';
import Composer from './Composer';

const meta: Meta<typeof Composer> = { component: Composer, title: 'Chat/Composer' };
export default meta;
type S = StoryObj<typeof Composer>;

export const Basic: S = { render: () => <Composer/> };
