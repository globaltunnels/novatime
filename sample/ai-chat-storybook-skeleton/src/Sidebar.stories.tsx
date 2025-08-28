
import type { Meta, StoryObj } from '@storybook/react';
import Sidebar from './Sidebar';
import { StoreProvider } from '../store';

const meta: Meta<typeof Sidebar> = { component: Sidebar, title: 'App/Sidebar' };
export default meta;
type S = StoryObj<typeof Sidebar>;

export const Basic: S = { render: () => <StoreProvider><div className="app"><Sidebar/></div></StoreProvider> };
